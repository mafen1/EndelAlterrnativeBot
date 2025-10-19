# soundgen.py
import os
import numpy as np
from scipy.io.wavfile import write
import io
import pytz
from datetime import datetime
import subprocess
from ffmpeg_auto import ensure_ffmpeg
import tempfile
import random

SAMPLE_RATE = 22050

# Хроматическая шкала
CHROMATIC_BASE = {
    "C": 261.63, "C#": 277.18, "D": 293.66, "D#": 311.13,
    "E": 329.63, "F": 349.23, "F#": 369.99, "G": 392.00,
    "G#": 415.30, "A": 440.00, "A#": 466.16, "B": 493.88
}
CHROMATIC_NOTES = list(CHROMATIC_BASE.values())
CHROMATIC_NAMES = list(CHROMATIC_BASE.keys())

PENTATONIC_MAJOR = {k: [CHROMATIC_BASE[n] for n in notes] for k, notes in {
    "C": ["C", "D", "E", "G", "A"],
    "G": ["G", "A", "B", "D", "E"],
    "D": ["D", "E", "F#", "A", "B"],
    "A": ["A", "B", "C#", "E", "F#"],
    "E": ["E", "F#", "G#", "B", "C#"],
    "B": ["B", "C#", "D#", "F#", "G#"],
    "F#": ["F#", "G#", "A#", "C#", "D#"],
    "Db": ["D#", "F", "G", "A#", "C"],
    "Ab": ["G#", "A#", "C", "D#", "F"],
    "Eb": ["D#", "F", "G", "A#", "C"],
    "Bb": ["A#", "C", "D", "F", "G"],
    "F": ["F", "G", "A", "C", "D"],
}.items()}

PENTATONIC_MINOR = {k: [CHROMATIC_BASE[n] for n in notes] for k, notes in {
    "A": ["A", "C", "D", "E", "G"],
    "E": ["E", "G", "A", "B", "D"],
    "B": ["B", "D", "E", "F#", "A"],
    "F#": ["F#", "A", "B", "C#", "E"],
    "Db": ["D#", "F", "G#", "A#", "C"],
    "Ab": ["G#", "B", "C#", "D#", "F#"],
    "Eb": ["D#", "F#", "G#", "A#", "C#"],
    "Bb": ["A#", "C#", "D#", "F", "G#"],
    "F": ["F", "A", "B", "C", "E"],
    "C": ["C", "D#", "F", "G", "A#"],
    "G": ["G", "A#", "C", "D", "F"],
    "D": ["D", "F", "G", "A", "C"],
}.items()}


def get_time_of_day(tz_name="UTC"):
    try:
        tz = pytz.timezone(tz_name)
    except:
        tz = pytz.utc
    hour = datetime.now(tz).hour
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "day"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"


def get_adaptive_params(time_of_day, mode, duration_sec):
    base_freq = 110.0
    if mode == "sleep":
        base_freq = 55.0
        params = {
            "drone_level": 0.08,
            "harmony_level": 0.04,
            "melody_level": 0.02,
            "bass_level": 0.03,
            "perc_level": 0.01,
            "noise_level": 0.01,
            "nature_level": 0.03,
            "tempo": 50,
            "key_shift": -2.0,
            "structure_change_interval": np.random.uniform(90, 150),
            "num_instruments": 2,
            "time_of_day_factor": 0.8 if time_of_day == "night" else 1.0,
            "melody_wave": "sine",
            "melody_adsr": (0.1, 0.2, 0.5, 1.5)
        }
    elif mode == "calm":
        params = {
            "drone_level": 0.10,
            "harmony_level": 0.06,
            "melody_level": 0.04,
            "bass_level": 0.04,
            "perc_level": 0.02,
            "noise_level": 0.02,
            "nature_level": 0.02,
            "tempo": 60,
            "key_shift": -1.0,
            "structure_change_interval": np.random.uniform(60, 100),
            "num_instruments": 3,
            "time_of_day_factor": 0.9 if time_of_day == "night" else 1.0,
            "melody_wave": "sine",
            "melody_adsr": (0.08, 0.15, 0.6, 1.2)
        }
    elif mode == "energy":
        params = {
            "drone_level": 0.08,
            "harmony_level": 0.08,
            "melody_level": 0.07,
            "bass_level": 0.06,
            "perc_level": 0.05,
            "noise_level": 0.03,
            "nature_level": 0.0,
            "tempo": 90,
            "key_shift": 2.0,
            "structure_change_interval": np.random.uniform(30, 60),
            "num_instruments": 4,
            "time_of_day_factor": 1.2 if time_of_day == "morning" else 1.0,
            "melody_wave": "piano",
            "melody_adsr": (0.005, 0.4, 0.15, 1.2)
        }
    elif mode == "deep":
        params = {
            "drone_level": 0.12,
            "harmony_level": 0.03,
            "melody_level": 0.01,
            "bass_level": 0.03,
            "perc_level": 0.01,
            "noise_level": 0.02,
            "nature_level": 0.01,
            "tempo": 60,
            "key_shift": -1.5,
            "structure_change_interval": np.random.uniform(120, 180),
            "num_instruments": 2,
            "time_of_day_factor": 1.0,
            "melody_wave": "sine",
            "melody_adsr": (0.2, 0.3, 0.4, 2.0)
        }
    elif mode == "creative":
        params = {
            "drone_level": 0.07,
            "harmony_level": 0.07,
            "melody_level": 0.06,
            "bass_level": 0.05,
            "perc_level": 0.04,
            "noise_level": 0.02,
            "nature_level": 0.0,
            "tempo": 75,
            "key_shift": 1.0,
            "structure_change_interval": np.random.uniform(40, 70),
            "num_instruments": 4,
            "time_of_day_factor": 1.1,
            "melody_wave": "pluck",
            "melody_adsr": (0.01, 0.2, 0.6, 0.8)
        }
    elif mode == "recovery":
        params = {
            "drone_level": 0.10,
            "harmony_level": 0.04,
            "melody_level": 0.02,
            "bass_level": 0.02,
            "perc_level": 0.01,
            "noise_level": 0.02,
            "nature_level": 0.04,
            "tempo": 55,
            "key_shift": -2.0,
            "structure_change_interval": np.random.uniform(100, 160),
            "num_instruments": 2,
            "time_of_day_factor": 0.9,
            "melody_wave": "pad",
            "melody_adsr": (0.5, 0.5, 0.3, 3.0)
        }
    else:  # focus
        params = {
            "drone_level": 0.10,
            "harmony_level": 0.06,
            "melody_level": 0.05,
            "bass_level": 0.05,
            "perc_level": 0.03,
            "noise_level": 0.025,
            "nature_level": 0.0,
            "tempo": 70,
            "key_shift": 0.0,
            "structure_change_interval": np.random.uniform(60, 110),
            "num_instruments": 3,
            "time_of_day_factor": 1.0,
            "melody_wave": "sine",
            "melody_adsr": (0.05, 0.1, 0.7, 0.3)
        }

    if time_of_day == "night":
        base_freq *= 0.944
        for k in ["drone_level", "harmony_level", "melody_level", "bass_level", "perc_level", "noise_level", "nature_level"]:
            params[k] *= 0.85
        params["tempo"] = max(40, params["tempo"] * 0.8)
        params["key_shift"] -= 1.0
    elif time_of_day == "morning":
        base_freq *= 1.059
        for k in ["drone_level", "harmony_level", "melody_level", "bass_level", "perc_level", "noise_level", "nature_level"]:
            params[k] *= 1.1
        params["tempo"] = min(120, params["tempo"] * 1.15)
        params["key_shift"] += 1.0

    return base_freq, params


def generate_envelope(length, attack=0.01, decay=0.3, sustain=0.2, release=1.0):
    if length == 0:
        return np.array([])
    attack_samples = int(attack * SAMPLE_RATE)
    decay_samples = int(decay * SAMPLE_RATE)
    release_samples = int(release * SAMPLE_RATE)
    sustain_samples = length - attack_samples - decay_samples - release_samples
    if sustain_samples < 0:
        return np.hanning(length)
    env = np.concatenate([
        np.linspace(0, 1, max(1, attack_samples)),
        np.linspace(1, sustain, max(1, decay_samples)),
        np.full(max(0, sustain_samples), sustain),
        np.linspace(sustain, 0, max(1, release_samples))
    ])
    if len(env) > length:
        env = env[:length]
    elif len(env) < length:
        env = np.pad(env, (0, length - len(env)), 'constant', constant_values=0)
    return env


def generate_piano_note(freq, duration):
    if duration <= 0:
        return np.array([])
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    mod_freq = freq * 2.5
    mod_index = 3.0
    modulator = np.sin(2 * np.pi * mod_freq * t)
    carrier = np.sin(2 * np.pi * freq * t + mod_index * modulator)
    noise_len = int(0.02 * SAMPLE_RATE)
    noise = np.zeros_like(t)
    if noise_len < len(t):
        noise[:noise_len] = np.random.randn(noise_len) * 0.5
        noise_env = np.exp(-np.linspace(0, 10, noise_len))
        noise[:noise_len] *= noise_env
    wave = carrier + noise
    env = generate_envelope(len(wave), attack=0.005, decay=0.4, sustain=0.15, release=1.2)
    wave *= env
    if np.max(np.abs(wave)) > 0:
        wave = wave / np.max(np.abs(wave)) * 0.9
    return wave


def generate_pluck(freq, duration):
    if duration <= 0:
        return np.array([])
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = np.sin(2 * np.pi * freq * t) * np.exp(-t * 3)
    return wave


def generate_pad(freq, duration):
    if duration <= 0:
        return np.array([])
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = np.sin(2 * np.pi * freq * t)
    # Добавим мягкую модуляцию
    lfo = np.sin(2 * np.pi * 0.3 * t)  # 0.3 Hz
    wave *= (1 + 0.2 * lfo)
    return wave


def generate_pink_noise(duration):
    white = np.random.randn(int(SAMPLE_RATE * duration))
    pink = np.cumsum(white)
    pink = pink / (np.max(np.abs(pink)) + 1e-6)
    return pink


def generate_nature_sound(sound_type="rain", duration=10):
    if sound_type == "rain":
        # Имитация дождя: случайные щелчки + фильтрованный шум
        total_samples = int(SAMPLE_RATE * duration)
        signal = np.zeros(total_samples)
        # Добавим капли
        drop_rate = 8  # капель в секунду
        num_drops = int(drop_rate * duration)
        for _ in range(num_drops):
            idx = random.randint(0, total_samples - 1)
            if idx + 100 < total_samples:
                drop = np.random.exponential(1, 100)
                signal[idx:idx+100] += drop * 0.05
        # Добавим фоновый шум
        noise = generate_pink_noise(duration) * 0.02
        signal += noise
        return signal
    else:  # forest
        total_samples = int(SAMPLE_RATE * duration)
        signal = np.zeros(total_samples)
        # Пение птиц: короткие синусы на высоких частотах
        for _ in range(int(2 * duration)):
            freq = random.uniform(2000, 5000)
            start = random.uniform(0, duration - 0.3)
            dur = random.uniform(0.1, 0.3)
            t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
            chirp = np.sin(2 * np.pi * freq * t) * np.hanning(len(t))
            idx_start = int(start * SAMPLE_RATE)
            idx_end = idx_start + len(chirp)
            if idx_end < total_samples:
                signal[idx_start:idx_end] += chirp * 0.03
        return signal


def generate_structure_phases(duration_sec, change_interval):
    phases = []
    start_time = 0
    while start_time < duration_sec:
        end_time = min(start_time + change_interval, duration_sec)
        phases.append((start_time, end_time))
        start_time = end_time
    return phases


def crossfade_arrays(a, b, fade_samples):
    if fade_samples <= 0 or len(a) < fade_samples or len(b) < fade_samples:
        return np.concatenate([a, b])
    fade_out = np.linspace(1, 0, fade_samples)
    fade_in = np.linspace(0, 1, fade_samples)
    a[-fade_samples:] *= fade_out
    b[:fade_samples] *= fade_in
    middle = a[-fade_samples:] + b[:fade_samples]
    return np.concatenate([a[:-fade_samples], middle, b[fade_samples:]])


def generate_session_structure(base_freq, duration_sec, params, time_of_day, mode, include_breaks=False):
    if include_breaks:
        work_duration = duration_sec * 0.83  # 50 мин → 42 мин работы + 8 мин тишины
        silence_duration = duration_sec - work_duration
    else:
        work_duration = duration_sec
        silence_duration = 0

    total_samples = int(SAMPLE_RATE * work_duration)
    audio_signal = np.zeros(total_samples)

    scale_type = PENTATONIC_MINOR if mode in ['sleep', 'calm', 'deep', 'recovery'] else PENTATONIC_MAJOR
    main_key = random.choice(list(scale_type.keys()))
    main_scale = scale_type[main_key]

    phases = generate_structure_phases(work_duration, params["structure_change_interval"])
    last_phase_signal = None

    for i, (start_time, end_time) in enumerate(phases):
        phase_duration = end_time - start_time
        start_idx = int(start_time * SAMPLE_RATE)
        end_idx = int(end_time * SAMPLE_RATE)
        end_idx = min(end_idx, total_samples)
        phase_length = end_idx - start_idx

        chord_degrees = [0, 2, 4]
        possible_degrees = [0, 1, 2, 3, 4, 5]
        chord_root_degree = random.choice(possible_degrees)
        chord_notes = []
        for degree in chord_degrees:
            scale_idx = (chord_root_degree + degree) % len(main_scale)
            chord_notes.append(main_scale[scale_idx] * (1 + params["key_shift"] / 100))

        phase_signal = np.zeros(phase_length)

        # Дрон
        drone_wave = generate_wave(base_freq, phase_duration, wave_type='sine', harmonic_levels=[0.1, 0.05])
        drone_wave = np.resize(drone_wave, phase_length)
        drone_env = generate_envelope(phase_length, attack=0.5, release=1.0)
        phase_signal += drone_wave * drone_env * params["drone_level"] * params["time_of_day_factor"]

        # Гармония
        harmony_wave = np.zeros(phase_length)
        for note_freq in chord_notes:
            note_wave = generate_wave(note_freq, phase_duration, wave_type='sine', harmonic_levels=[0.3, 0.1])
            note_wave = np.resize(note_wave, phase_length)
            harmony_wave += note_wave
        harmony_env = generate_envelope(phase_length, attack=0.2, release=0.8)
        phase_signal += harmony_wave * harmony_env * params["harmony_level"] * params["time_of_day_factor"]

        # Мелодия
        melody_wave = np.zeros(phase_length)
        note_duration = 60 / params["tempo"]
        num_notes = int(phase_duration / note_duration)
        if num_notes > 0:
            extended_scale = main_scale + [n * 2 for n in main_scale]
            extended_scale = [f for f in extended_scale if f < 800]
            for j in range(num_notes):
                melody_note_freq = random.choice(extended_scale) * (1 + params["key_shift"] / 100)
                start_time_note = j * note_duration
                end_time_note = min(start_time_note + note_duration, phase_duration)
                note_dur_sec = end_time_note - start_time_note
                if params["melody_wave"] == "piano":
                    note_signal = generate_piano_note(melody_note_freq, note_dur_sec)
                elif params["melody_wave"] == "pluck":
                    note_signal = generate_pluck(melody_note_freq, note_dur_sec)
                    note_env = generate_envelope(len(note_signal), *params["melody_adsr"])
                    note_signal *= note_env
                elif params["melody_wave"] == "pad":
                    note_signal = generate_pad(melody_note_freq, note_dur_sec)
                    note_env = generate_envelope(len(note_signal), *params["melody_adsr"])
                    note_signal *= note_env
                else:
                    note_signal = generate_wave(melody_note_freq, note_dur_sec, wave_type='sine', harmonic_levels=[0.2, 0.1])
                    note_env = generate_envelope(len(note_signal), *params["melody_adsr"])
                    note_signal *= note_env
                start_idx_note = int(start_time_note * SAMPLE_RATE)
                end_idx_note = start_idx_note + len(note_signal)
                if end_idx_note > phase_length:
                    note_signal = note_signal[:phase_length - start_idx_note]
                    end_idx_note = phase_length
                if start_idx_note < phase_length:
                    melody_wave[start_idx_note:end_idx_note] += note_signal
        phase_signal += melody_wave * params["melody_level"] * params["time_of_day_factor"]

        # Бас
        bass_freq = chord_notes[0] / 2
        bass_wave = generate_wave(bass_freq, phase_duration, wave_type='sine', harmonic_levels=[0.4, 0.2])
        bass_wave = np.resize(bass_wave, phase_length)
        bass_env = generate_envelope(phase_length, attack=0.1, release=0.6)
        phase_signal += bass_wave * bass_env * params["bass_level"] * params["time_of_day_factor"]

        # Перкуссия
        if params["perc_level"] > 0:
            tick_interval = 60 / params["tempo"]
            t_tick = np.arange(0, phase_duration, tick_interval)
            for tick_time in t_tick:
                tick_idx = int(tick_time * SAMPLE_RATE)
                if tick_idx < phase_length:
                    tick_signal_len = int(0.05 * SAMPLE_RATE)
                    tick_signal = np.zeros(tick_signal_len)
                    tick_signal[:int(0.001 * SAMPLE_RATE)] = np.random.randn(int(0.001 * SAMPLE_RATE))
                    tick_env = generate_envelope(tick_signal_len, attack=0.001, release=0.04)
                    tick_signal *= tick_env * params["perc_level"] * params["time_of_day_factor"]
                    tick_end_idx = min(tick_idx + len(tick_signal), phase_length)
                    phase_signal[tick_idx:tick_end_idx] += tick_signal[:tick_end_idx - tick_idx]

        # Плавный переход между фазами
        if last_phase_signal is not None:
            fade_samples = min(4096, len(last_phase_signal), len(phase_signal))
            combined = crossfade_arrays(last_phase_signal, phase_signal, fade_samples)
            audio_signal[start_idx - len(last_phase_signal):start_idx + len(phase_signal) - fade_samples] = combined
        else:
            audio_signal[start_idx:end_idx] = phase_signal

        last_phase_signal = phase_signal

    # Шум
    pink = generate_pink_noise(work_duration)
    audio_signal += pink * params["noise_level"] * params["time_of_day_factor"]

    # Природа
    if params["nature_level"] > 0:
        nature_type = "rain" if mode in ["sleep", "recovery"] else "forest"
        nature = generate_nature_sound(nature_type, work_duration)
        audio_signal += nature * params["nature_level"]

    audio_signal = np.clip(audio_signal, -1, 1)

    # Добавляем тишину в конец, если нужно
    if silence_duration > 0:
        silence_samples = int(SAMPLE_RATE * silence_duration)
        audio_signal = np.concatenate([audio_signal, np.zeros(silence_samples)])

    return audio_signal


def generate_wave(freq, duration, wave_type='sine', harmonic_levels=None):
    if duration <= 0:
        return np.array([])
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = np.zeros_like(t)
    if wave_type == 'sine':
        wave = np.sin(2 * np.pi * freq * t)
    elif wave_type == 'saw':
        wave = 2 * (t * freq - np.floor(0.5 + t * freq))
    elif wave_type == 'square':
        wave = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave_type == 'triangle':
        wave = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    else:
        wave = np.sin(2 * np.pi * freq * t)
    if harmonic_levels:
        for i, level in enumerate(harmonic_levels):
            if level > 0:
                harmonic_freq = freq * (i + 2)
                wave += level * np.sin(2 * np.pi * harmonic_freq * t)
    if np.max(np.abs(wave)) > 0:
        wave = wave / np.max(np.abs(wave)) * 0.9
    return wave


def generate_wav(mode="focus", duration_sec=3000, tz_name="UTC", forced_time_of_day=None, include_breaks=False):
    time_of_day = forced_time_of_day if forced_time_of_day else get_time_of_day(tz_name)
    base_freq, params = get_adaptive_params(time_of_day, mode, duration_sec)
    audio = generate_session_structure(base_freq, duration_sec, params, time_of_day, mode, include_breaks=include_breaks)
    fade_samples = int(4 * SAMPLE_RATE)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    audio_int16 = (audio * 32767).astype(np.int16)
    buffer = io.BytesIO()
    write(buffer, SAMPLE_RATE, audio_int16)
    buffer.seek(0)
    return buffer, time_of_day


def wav_to_mp3(wav_bytes: bytes) -> bytes:
    ffmpeg_path = ensure_ffmpeg()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav.write(wav_bytes)
        temp_wav_path = temp_wav.name
    temp_mp3_path = temp_wav_path.replace(".wav", ".mp3")
    try:
        proc = subprocess.run(
            [
                ffmpeg_path,
                "-i", temp_wav_path,
                "-f", "mp3",
                "-b:a", "128k",
                "-y",
                temp_mp3_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg error: {proc.stderr.decode()}")
        with open(temp_mp3_path, "rb") as f:
            mp3_bytes = f.read()
        return mp3_bytes
    finally:
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)