# ffmpeg_auto.py
import os
import sys

# Удаляем проблемные переменные окружения для корректной работы SSL
for key in ['SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']:
    os.environ.pop(key, None)

import requests
import zipfile
import io
from tqdm import tqdm

FFMPEG_DIR = os.path.join(os.path.dirname(__file__), "ffmpeg")
FFMPEG_BIN = os.path.join(FFMPEG_DIR, "bin", "ffmpeg.exe")


def ensure_ffmpeg():
    """Скачивает и распаковывает ffmpeg, если он отсутствует."""
    if os.path.exists(FFMPEG_BIN):
        print("✅ ffmpeg уже установлен.")
        return FFMPEG_BIN

    print("📦 ffmpeg не найден. Скачиваю (размер ~70 МБ)...")
    # --- ИСПРАВЛЕНО: Удалены все пробелы в конце URL ---
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        zip_buffer = io.BytesIO()

        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Скачивание") as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Защита от пустых чанков
                    zip_buffer.write(chunk)
                    pbar.update(len(chunk))

        print("Распаковка...")
        zip_buffer.seek(0)

        with zipfile.ZipFile(zip_buffer) as zf:
            # Определяем корневую папку в архиве
            namelist = zf.namelist()
            if not namelist:
                raise ValueError("Архив пуст")

            root_dir = namelist[0].split('/')[0]
            bin_path = f"{root_dir}/bin/ffmpeg.exe"

            if bin_path not in namelist:
                raise FileNotFoundError(f"Файл {bin_path} не найден в архиве")

            # Создаём целевую директорию, если её нет
            os.makedirs(FFMPEG_DIR, exist_ok=True)

            # Извлекаем только нужный файл (и его родительские папки)
            zf.extract(bin_path, FFMPEG_DIR)

            # Перемещаем bin в корень FFMPEG_DIR
            extracted_bin_dir = os.path.join(FFMPEG_DIR, root_dir, "bin")
            target_bin_dir = os.path.join(FFMPEG_DIR, "bin")

            if os.path.exists(target_bin_dir):
                import shutil
                shutil.rmtree(target_bin_dir)

            os.rename(extracted_bin_dir, target_bin_dir)

            # Удаляем оставшуюся папку root_dir
            root_full_path = os.path.join(FFMPEG_DIR, root_dir)
            if os.path.exists(root_full_path) and os.path.isdir(root_full_path):
                import shutil
                shutil.rmtree(root_full_path)

        print("✅ ffmpeg установлен в ./ffmpeg/")
        return FFMPEG_BIN

    except Exception as e:
        print(f"❌ Ошибка при установке ffmpeg: {e}")
        sys.exit(1)