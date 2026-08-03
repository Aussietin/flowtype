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
