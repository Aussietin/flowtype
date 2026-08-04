"""
flowtype — local hold-to-talk dictation, no subscription.

Hold the hotkey, speak, release — the transcript gets pasted at your cursor.
Runs entirely on-device via faster-whisper (CTranslate2 Whisper). No audio
or text ever leaves the machine.

Usage:
    venv\\Scripts\\pythonw.exe flowtype.py   (background, tray icon, no console)
    venv\\Scripts\\python.exe flowtype.py    (console visible, for debugging)

Hold Right Ctrl to talk, release to paste. Tray icon: grey = idle, red =
recording, amber = transcribing, flashing red "!" = something errored (also
fires a toast). Right-click the tray icon to quit, or tap Esc twice as a
fallback (works even without the console open).
"""
import ctypes
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

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
MAX_RECORD_SECONDS = 60  # safety valve — auto-stops a stuck/forgotten hold
CLIPBOARD_RESTORE_DELAY = 0.25  # let the paste land before restoring old clipboard
TRANSCRIPT_LOG = Path(__file__).resolve().parent / "logs" / "transcripts.jsonl"

_recording = False
_frames: list[np.ndarray] = []
_stream: sd.InputStream | None = None
_lock = threading.Lock()
_status = "idle"  # idle | recording | transcribing
_session = 0  # bumped on each start_recording, lets the watchdog tell old/new apart
_error: str | None = None  # set on a failure, surfaced once by poll() as a toast


def _report_error(msg: str):
    global _error, _status
    print(f"[flowtype] ERROR: {msg}")
    with _lock:
        _error = msg
        _status = "idle"


def _audio_callback(indata, _frames_count, _time_info, _status_flags):
    with _lock:
        if _recording:
            _frames.append(indata.copy())


def _watchdog(model: WhisperModel, session: int):
    time.sleep(MAX_RECORD_SECONDS)
    with _lock:
        expired = _recording and _session == session
    if expired:
        print(f"[flowtype] held past {MAX_RECORD_SECONDS}s, auto-stopping")
        stop_recording_and_transcribe(model)


def start_recording(model: WhisperModel):
    global _recording, _frames, _stream, _status, _session
    with _lock:
        if _recording:
            return
        _recording = True
        _frames = []
        _status = "recording"
        _session += 1
        session = _session
    try:
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=_audio_callback
        )
        stream.start()
    except Exception as e:
        with _lock:
            _recording = False
        _report_error(f"couldn't open microphone: {e}")
        return
    _stream = stream
    threading.Thread(target=_watchdog, args=(model, session), daemon=True).start()
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
        _log_transcript(text)
        _paste(text)
    except Exception as e:
        _report_error(f"transcription failed: {e}")
    finally:
        with _lock:
            _status = "idle"


def _log_transcript(text: str):
    """Append every transcript to a local JSONL log — raw material for SOPs
    later, costs nothing to keep. Never leaves the machine."""
    try:
        TRANSCRIPT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {"ts": datetime.now(timezone.utc).isoformat(), "text": text}
        with open(TRANSCRIPT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[flowtype] transcript log write failed (non-fatal): {e}")


def _paste(text: str):
    try:
        old_clip = pyperclip.paste()
    except Exception:
        old_clip = None

    pyperclip.copy(text)
    keyboard.send("ctrl+v")

    if old_clip is not None:
        def _restore():
            time.sleep(CLIPBOARD_RESTORE_DELAY)
            try:
                pyperclip.copy(old_clip)
            except Exception:
                pass
        threading.Thread(target=_restore, daemon=True).start()


def poll() -> State:
    global _error
    with _lock:
        error, _error = _error, None
        status = _status

    if error:
        return State(fraction=1.0, text="!", color=RED,
                     tooltip=f"flowtype — error: {error}",
                     menu_label=f"Error: {error}",
                     notify=("flowtype error", error))
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


def _acquire_singleton_or_exit():
    """Windows named mutex — refuse to start a second instance."""
    kernel32 = ctypes.windll.kernel32
    ERROR_ALREADY_EXISTS = 183
    kernel32.CreateMutexW(None, False, "Global\\flowtype_singleton")
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        ctypes.windll.user32.MessageBoxW(
            0, "flowtype is already running (check the system tray).",
            "flowtype", 0x40)
        sys.exit(0)


def main():
    _acquire_singleton_or_exit()

    default_input = sd.query_devices(kind="input")
    print(f"[flowtype] mic: {default_input['name']}")

    print(f"[flowtype] loading {MODEL_SIZE} model ({DEVICE}/{COMPUTE_TYPE})...")
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    print(f"[flowtype] ready. Hold [{HOTKEY}] to talk, release to paste. "
          f"Tap [{QUIT_KEY}] twice to quit.")

    keyboard.on_press_key(HOTKEY, lambda _: start_recording(model))
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
