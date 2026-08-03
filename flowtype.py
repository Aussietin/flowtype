"""
flowtype — local hold-to-talk dictation, no subscription.

Hold the hotkey, speak, release — the transcript gets pasted at your cursor.
Runs entirely on-device via faster-whisper (CTranslate2 Whisper). No audio
or text ever leaves the machine.

Usage:
    venv\\Scripts\\python.exe flowtype.py
    (hold Right Ctrl to talk, release to transcribe + paste; Esc twice to quit)
"""
import queue
import sys
import threading
import time

import keyboard
import numpy as np
import pyperclip
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
HOTKEY = "right ctrl"
QUIT_KEY = "esc"
MODEL_SIZE = "base.en"  # tiny.en / base.en / small.en — bigger = more accurate, slower
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

_recording = False
_frames: list[np.ndarray] = []
_stream: sd.InputStream | None = None
_lock = threading.Lock()


def _audio_callback(indata, _frames_count, _time_info, _status):
    with _lock:
        if _recording:
            _frames.append(indata.copy())


def start_recording():
    global _recording, _frames, _stream
    with _lock:
        if _recording:
            return
        _recording = True
        _frames = []
    _stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=_audio_callback
    )
    _stream.start()
    print("[flowtype] listening...")


def stop_recording_and_transcribe(model: WhisperModel):
    global _recording, _stream
    with _lock:
        if not _recording:
            return
        _recording = False
    if _stream is not None:
        _stream.stop()
        _stream.close()
        _stream = None

    if not _frames:
        print("[flowtype] no audio captured")
        return

    audio = np.concatenate(_frames, axis=0).flatten()
    duration = len(audio) / SAMPLE_RATE
    if duration < 0.3:
        print("[flowtype] clip too short, skipped")
        return

    print(f"[flowtype] transcribing {duration:.1f}s...")
    segments, _info = model.transcribe(audio, language="en", vad_filter=True)
    text = "".join(segment.text for segment in segments).strip()

    if not text:
        print("[flowtype] heard nothing")
        return

    print(f"[flowtype] -> {text}")
    pyperclip.copy(text)
    keyboard.send("ctrl+v")


def main():
    print(f"[flowtype] loading {MODEL_SIZE} model ({DEVICE}/{COMPUTE_TYPE})...")
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    print(f"[flowtype] ready. Hold [{HOTKEY}] to talk, release to paste. "
          f"Tap [{QUIT_KEY}] twice to quit.")

    keyboard.on_press_key(HOTKEY, lambda _: start_recording())
    keyboard.on_release_key(HOTKEY, lambda _: threading.Thread(
        target=stop_recording_and_transcribe, args=(model,), daemon=True
    ).start())

    last_esc = 0.0

    def _on_esc(_):
        nonlocal last_esc
        now = time.time()
        if now - last_esc < 0.5:
            print("[flowtype] quitting")
            keyboard.unhook_all()
            sys.exit(0)
        last_esc = now

    keyboard.on_press_key(QUIT_KEY, _on_esc)

    keyboard.wait()


if __name__ == "__main__":
    main()
