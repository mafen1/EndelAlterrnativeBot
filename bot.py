# bot.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import asyncio
from soundgen import generate_wav, wav_to_mp3

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8366694012:AAGQifzu4KjYwMGSRbLoupEtecivDH-4FA0"

# Доступные длительности в минутах
AVAILABLE_DURATIONS = [5, 10, 20, 25, 30, 35, 40, 50]

# Словарь для перевода режимов в понятные названия
MODE_NAMES = {
    "focus": "Концентрация",
    "sleep": "Сон",
    "calm": "Спокойствие",
    "energy": "Энергия",
    "deep": "Глубокая работа",
    "creative": "Креатив",
    "recovery": "Восстановление"
}

# Словарь для перевода времени суток
TIME_NAMES = {
    "morning": "Утро",
    "day": "День",
    "evening": "Вечер",
    "night": "Ночь"
}

async def ask_time_of_day(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    """Отправляет сообщение с кнопками для выбора времени суток."""
    keyboard = []
    row = []
    for time_key, time_name in TIME_NAMES.items():
        callback_data = f"tod_{mode}|{time_key}"
        button = InlineKeyboardButton(time_name, callback_data=callback_data)
        row.append(button)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🌅 Выберите время суток для режима *{MODE_NAMES.get(mode, mode)}*:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ask_duration(update_or_message, context: ContextTypes.DEFAULT_TYPE, mode: str, forced_time_of_day: str):
    """Отправляет сообщение с кнопками для выбора длительности и опции перерывов."""
    context.user_data['selected_mode'] = mode
    context.user_data['selected_time_of_day'] = forced_time_of_day

    # Кнопки длительности
    keyboard = []
    row = []
    for i, duration in enumerate(AVAILABLE_DURATIONS):
        callback_data = f"duration_{duration}"
        button = InlineKeyboardButton(f"{duration} мин", callback_data=callback_data)
        row.append(button)
        if len(row) == 4 or i == len(AVAILABLE_DURATIONS) - 1:
            keyboard.append(row)
            row = []

    # Кнопка "С перерывами"
    keyboard.append([InlineKeyboardButton("⏸ С перерывами (тишина в конце)", callback_data="with_breaks")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"⏱ Выберите длительность сессии для режима *{MODE_NAMES.get(mode, mode)}* и времени *{TIME_NAMES.get(forced_time_of_day)}*:"
    if hasattr(update_or_message, 'message'):
        await update_or_message.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update_or_message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Обработка выбора времени суток
    if data.startswith("tod_"):
        parts = data.split("|")
        if len(parts) != 2:
            await query.edit_message_text("❌ Неверный формат данных.")
            return
        mode, time_of_day = parts[0][4:], parts[1]
        if mode not in MODE_NAMES or time_of_day not in TIME_NAMES:
            await query.edit_message_text("❌ Неверные параметры.")
            return
        await query.edit_message_text(f"⏳ Выбрано время: {TIME_NAMES[time_of_day]}. Выбираю длительность...")
        await ask_duration(query.message, context, mode, time_of_day)
        return

    # Обработка выбора длительности
    if data.startswith("duration_"):
        try:
            duration_min = int(data[9:])
            if duration_min not in AVAILABLE_DURATIONS:
                raise ValueError
        except ValueError:
            await query.edit_message_text("❌ Неверная длительность.")
            return

        mode = context.user_data.get('selected_mode')
        time_of_day = context.user_data.get('selected_time_of_day')
        if not mode or not time_of_day:
            await query.edit_message_text("❌ Не удалось получить данные. Попробуйте снова.")
            return

        # Сохраняем параметры
        context.user_data['selected_duration_min'] = duration_min
        context.user_data['include_breaks'] = False  # по умолчанию без перерывов

        await query.edit_message_text(f"⏳ Генерирую {duration_min} мин для '{MODE_NAMES[mode]}' ({TIME_NAMES[time_of_day]})...")
        await send_sound(query.message, context, mode, time_of_day, duration_min, include_breaks=False)
        return

    # Обработка кнопки "С перерывами"
    if data == "with_breaks":
        mode = context.user_data.get('selected_mode')
        time_of_day = context.user_data.get('selected_time_of_day')
        if not mode or not time_of_day:
            await query.edit_message_text("❌ Не удалось получить данные. Попробуйте снова.")
            return

        # Запрашиваем длительность ещё раз, но теперь с флагом перерывов
        context.user_data['include_breaks_flag'] = True
        await query.edit_message_text("⏸ Включены перерывы. Выберите длительность:")
        await ask_duration(query.message, context, mode, time_of_day)
        return

    # Если длительность выбрана после нажатия "С перерывами"
    if data.startswith("duration_") and context.user_data.get('include_breaks_flag'):
        try:
            duration_min = int(data[9:])
            if duration_min not in AVAILABLE_DURATIONS:
                raise ValueError
        except ValueError:
            await query.edit_message_text("❌ Неверная длительность.")
            return

        mode = context.user_data.get('selected_mode')
        time_of_day = context.user_data.get('selected_time_of_day')
        if not mode or not time_of_day:
            await query.edit_message_text("❌ Не удалось получить данные.")
            return

        context.user_data['selected_duration_min'] = duration_min
        context.user_data['include_breaks'] = True
        del context.user_data['include_breaks_flag']

        await query.edit_message_text(f"⏳ Генерирую {duration_min} мин с перерывами для '{MODE_NAMES[mode]}' ({TIME_NAMES[time_of_day]})...")
        await send_sound(query.message, context, mode, time_of_day, duration_min, include_breaks=True)
        return

    await query.edit_message_text("❌ Неизвестная команда.")

async def send_sound(message, context: ContextTypes.DEFAULT_TYPE, mode: str, forced_time_of_day: str, duration_min: int, include_breaks: bool = False):
    user = message.from_user
    duration_sec = duration_min * 60
    time_display = TIME_NAMES.get(forced_time_of_day, "Авто")

    status_msg = await message.reply_text(
        f"🧠 Генерирую {MODE_NAMES.get(mode, mode)} звук (~{duration_min} мин) для '{time_display}'...\n"
        "Сначала создам WAV, затем конвертирую в MP3."
    )

    try:
        loop = asyncio.get_event_loop()

        await status_msg.edit_text(
            f"🧠 Генерирую {MODE_NAMES.get(mode, mode)} звук (~{duration_min} мин) для '{time_display}'...\n"
            "Создаю WAV..."
        )

        wav_buffer, actual_time_of_day = await loop.run_in_executor(
            None, generate_wav, mode, duration_sec, "UTC", forced_time_of_day, include_breaks
        )
        wav_bytes = wav_buffer.getvalue()
        logging.info(f"WAV сгенерирован: {len(wav_bytes) / (1024 ** 2):.1f} МБ")

        await status_msg.edit_text(
            f"🧠 Генерирую {MODE_NAMES.get(mode, mode)} звук (~{duration_min} мин) для '{time_display}'...\n"
            "Конвертирую в MP3..."
        )

        mp3_bytes = await loop.run_in_executor(None, wav_to_mp3, wav_bytes)
        logging.info(f"MP3 готов: {len(mp3_bytes) / (1024 ** 2):.1f} МБ")

        await status_msg.delete()

        filename = f"endel_{mode}_{actual_time_of_day}_{duration_min}min{'_breaks' if include_breaks else ''}.mp3"
        await message.reply_audio(
            audio=mp3_bytes,
            filename=filename,
            title=f"Endel-like {MODE_NAMES.get(mode, mode)} ({duration_min} мин)",
            performer="StudyBot",
            caption=f"🎧 Режим: {MODE_NAMES.get(mode, mode)}\n"
                    f"Время: {TIME_NAMES.get(actual_time_of_day, actual_time_of_day)}\n"
                    f"Длительность: ~{duration_min} мин\n"
                    f"{'⏸ С перерывами' if include_breaks else '▶ Без перерывов'}"
        )

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        try:
            await status_msg.delete()
        except:
            pass
        await message.reply_text(f"❌ Ошибка: {str(e)[:200]}")

# --- Обработчики режимов ---
async def focus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_time_of_day(update, context, "focus")

async def sleep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_time_of_day(update, context, "sleep")

async def calm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_time_of_day(update, context, "calm")

async def energy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_time_of_day(update, context, "energy")

async def deep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_time_of_day(update, context, "deep")

async def creative(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_time_of_day(update, context, "creative")

async def recovery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_time_of_day(update, context, "recovery")

# --- Обработчики времени суток (режим focus по умолчанию) ---
async def morning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_duration(update, context, "focus", "morning")

async def day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_duration(update, context, "focus", "day")

async def evening(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_duration(update, context, "focus", "evening")

async def night(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_duration(update, context, "focus", "night")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 Endel-бот с MP3 (авто-установка ffmpeg)\n\n"
        "*Режимы:*\n"
        "/focus — для концентрации\n"
        "/deep — глубокая аналитика\n"
        "/creative — креативные задачи\n"
        "/recovery — восстановление после нагрузки\n"
        "/sleep — для сна\n"
        "/calm — для спокойствия\n"
        "/energy — для энергии\n\n"
        "*Быстрый выбор (режим фокуса):*\n"
        "/morning — Утро\n"
        "/day — День\n"
        "/evening — Вечер\n"
        "/night — Ночь\n\n"
        "Выберите режим → время суток → длительность → (опц. перерывы)."
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("focus", focus))
    app.add_handler(CommandHandler("deep", deep))
    app.add_handler(CommandHandler("creative", creative))
    app.add_handler(CommandHandler("recovery", recovery))
    app.add_handler(CommandHandler("sleep", sleep))
    app.add_handler(CommandHandler("calm", calm))
    app.add_handler(CommandHandler("energy", energy))
    app.add_handler(CommandHandler("morning", morning))
    app.add_handler(CommandHandler("day", day))
    app.add_handler(CommandHandler("evening", evening))
    app.add_handler(CommandHandler("night", night))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()

if __name__ == "__main__":
    main()