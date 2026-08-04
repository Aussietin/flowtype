"""
flowtype — local hold-to-talk dictation, no subscription.

Hold the hotkey, speak, release — the transcript gets pasted at your cursor.
Runs entirely on-device via faster-whisper (CTranslate2 Whisper). No audio
or text ever leaves the machine. Settings live in config.json.

Usage:
    venv\\Scripts\\pythonw.exe flowtype.py   (background, tray icon, no console)
    venv\\Scripts\\python.exe flowtype.py    (console visible, for debugging)

Hold the configured hotkey(s) to talk, release to paste. Tray icon: grey = idle, red =
recording, amber = transcribing, blue = LLM cleanup pass (if enabled),
flashing red "!" = something errored (also fires a toast). Right-click the
tray icon to quit, or tap Esc twice as a fallback (works even without the
console open).
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

import llm_cleanup
from config import load_config
from tray_indicator import Indicator, State, GREY, RED, AMBER, BLUE

CFG = load_config()
_hotkey_display = " / ".join(CFG.hotkeys)
SAMPLE_RATE = 16000
TRANSCRIPT_LOG = Path(__file__).resolve().parent / "logs" / "transcripts.jsonl"

_recording = False
_frames: list[np.ndarray] = []
_stream: sd.InputStream | None = None
_lock = threading.Lock()
_status = "idle"  # idle | recording | transcribing | cleaning
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
    time.sleep(CFG.max_record_seconds)
    with _lock:
        expired = _recording and _session == session
    if expired:
        print(f"[flowtype] held past {CFG.max_record_seconds}s, auto-stopping")
        stop_recording_and_transcribe(model)


def _open_persistent_stream() -> sd.InputStream | None:
    """Opened once at startup and left running for the app's lifetime.
    Opening an audio device has real latency (tens-hundreds of ms) — doing
    it fresh on every hotkey press clipped the first ~0.1-0.3s of speech,
    confirmed 2026-08-04 (a dictation's opening words were reliably lost).
    Keeping one stream open means start_recording() just flips a flag —
    the callback is already running, so capture begins on the very next
    audio buffer instead of waiting on device init.

    Tradeoff: Windows shows its "microphone in use" indicator the whole
    time flowtype runs, not just while actively recording. Traded
    deliberately for zero-latency capture start.
    """
    try:
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=_audio_callback
        )
        stream.start()
        return stream
    except Exception as e:
        _report_error(f"couldn't open microphone: {e}")
        return None


def start_recording(model: WhisperModel):
    global _recording, _frames, _status, _session
    if _stream is None:
        _report_error("no microphone available")
        return
    with _lock:
        if _recording:
            return
        _recording = True
        _frames = []
        _status = "recording"
        _session += 1
        session = _session
    threading.Thread(target=_watchdog, args=(model, session), daemon=True).start()
    print("[flowtype] listening...")


def stop_recording_and_transcribe(model: WhisperModel):
    global _recording, _status
    with _lock:
        if not _recording:
            return
        _recording = False
        _status = "transcribing"

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

        if CFG.llm_cleanup.enabled:
            with _lock:
                _status = "cleaning"
            cleaned = llm_cleanup.clean_up(text, CFG.llm_cleanup)
            if cleaned != text:
                print(f"[flowtype] cleaned -> {cleaned}")
            text = cleaned

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
            time.sleep(CFG.clipboard_restore_delay)
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
    if status == "cleaning":
        return State(fraction=1.0, text="✎", color=BLUE,
                     tooltip="flowtype — cleaning up with local LLM...",
                     menu_label="Cleaning up (LLM pass)...")
    return State(fraction=1.0, text="FT", color=GREY,
                 tooltip=f"flowtype — idle (hold {_hotkey_display} to talk)",
                 menu_label=f"Idle — hold {_hotkey_display} to talk")


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
    global _stream
    _acquire_singleton_or_exit()

    default_input = sd.query_devices(kind="input")
    print(f"[flowtype] mic: {default_input['name']}")

    _stream = _open_persistent_stream()
    if _stream is None:
        print("[flowtype] starting anyway so the tray shows the error — "
              "recording will fail until a mic is available")

    print(f"[flowtype] loading {CFG.model_size} model ({CFG.device}/{CFG.compute_type})...")
    model = WhisperModel(CFG.model_size, device=CFG.device, compute_type=CFG.compute_type)
    print(f"[flowtype] ready. Hold [{_hotkey_display}] to talk, release to paste. "
          f"Tap [{CFG.quit_key}] twice to quit. "
          f"LLM cleanup: {'on' if CFG.llm_cleanup.enabled else 'off'}")

    for key in CFG.hotkeys:
        keyboard.on_press_key(key, lambda _: start_recording(model))
        keyboard.on_release_key(key, lambda _: threading.Thread(
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

    keyboard.on_press_key(CFG.quit_key, _on_esc)

    Indicator("flowtype", poll, poll_seconds=1).run()


if __name__ == "__main__":
    main()
