"""
flowtype — local hold-to-talk dictation, no subscription.

Hold the hotkey, speak, release — the transcript gets pasted at your cursor.
Runs entirely on-device via faster-whisper (CTranslate2 Whisper). No audio
or text ever leaves the machine.

Usage:
    venv\\Scripts\\pythonw.exe flowtype.py   (background, tray icon, no console)
    venv\\Scripts\\python.exe flowtype.py    (console visible, for debugging)

Hold Right Ctrl to talk, release to paste. Tray icon: grey = idle, red =
recording, amber = transcribing. Right-click the tray icon to quit, or tap
Esc twice as a fallback (works even without the console open).
"""
import os
import sys
import threading
import time

# pythonw.exe has no console attached, so sys.stdout/stderr are None — any
# print() would crash on the first call. Redirect to devnull so logging is a
# no-op instead of a startup crash.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import keyboard
import numpy as np
import pyperclip
import sounddevice as sd
from faster_whisper import WhisperModel

from tray_indicator import Indicator, State, GREY, RED, AMBER

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
_status = "idle"  # idle | recording | transcribing


def _audio_callback(indata, _frames_count, _time_info, _status_flags):
    with _lock:
        if _recording:
            _frames.append(indata.copy())


def start_recording():
    global _recording, _frames, _stream, _status
    with _lock:
        if _recording:
            return
        _recording = True
        _frames = []
        _status = "recording"
    _stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=_audio_callback
    )
    _stream.start()
    print("[flowtype] listening...")


def stop_recording_and_transcribe(model: WhisperModel):
    global _recording, _stream, _status
    with _lock:
        if not _recording:
            return
        _recording = False
        _status = "transcribing"
    if _stream is not None:
        _stream.stop()
        _stream.close()
        _stream = None

    try:
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
    finally:
        with _lock:
            _status = "idle"


def poll() -> State:
    status = _status
    if status == "recording":
        return State(fraction=1.0, text="●", color=RED,
                     tooltip="flowtype — recording...",
                     menu_label="Recording...")
    if status == "transcribing":
        return State(fraction=1.0, text="…", color=AMBER,
                     tooltip="flowtype — transcribing...",
                     menu_label="Transcribing...")
    return State(fraction=1.0, text="FT", color=GREY,
                 tooltip=f"flowtype — idle (hold {HOTKEY} to talk)",
                 menu_label="Idle — hold Right Ctrl to talk")


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
            os._exit(0)  # hard exit — also tears down the tray icon's loop
        last_esc = now

    keyboard.on_press_key(QUIT_KEY, _on_esc)

    Indicator("flowtype", poll, poll_seconds=1).run()


if __name__ == "__main__":
    main()
