# flowtype

Local hold-to-talk dictation. A Wispr Flow clone with no subscription and no
audio leaving the machine — transcription runs on-device via
[faster-whisper](https://github.com/SYSTRAN/faster-whisper).

## Setup

```
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

## Run

```
venv\Scripts\python.exe flowtype.py
```

Hold **Right Ctrl**, speak, release — the transcript is pasted at your
cursor in whatever window has focus. Tap **Esc** twice to quit.

## Notes

- First run downloads the `base.en` Whisper model (~150MB) to the HF cache.
- Model size / hotkey are constants at the top of `flowtype.py` — bump to
  `small.en` for better accuracy at the cost of latency.
- No cleanup LLM pass yet (Wispr Flow polishes filler words/punctuation via
  an LLM) — raw Whisper output only for now.
- Clipboard is saved and restored around the paste — dictating doesn't
  destroy whatever you had copied.
- Only one instance can run at a time (Windows named mutex) — a second
  launch shows a message box and exits instead of double-pasting.
- A held hotkey auto-stops and transcribes after 60s (`MAX_RECORD_SECONDS`)
  so a forgotten hold can't run away with memory.
- Every transcript is appended to `logs/transcripts.jsonl` (gitignored,
  local only) — raw material for turning into SOPs later.
- Mic-open and transcription failures surface as a red "!" tray icon + a
  one-shot toast instead of failing silently.

## Tests

```
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\python.exe -m pytest test_flowtype.py -v
```

Covers the failure modes above (clipboard restore, mic-open failure,
transcription failure, double-stop safety, the watchdog, transcript
logging, the singleton mutex) — not a full suite, just what's broken or
could break.
