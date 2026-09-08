# flowtype

Local hold-to-talk dictation. A Wispr Flow clone with no subscription and no
audio leaving the machine — transcription runs on-device via
[faster-whisper](https://github.com/SYSTRAN/faster-whisper). Zero network
calls of its own; the only network activity anywhere is faster-whisper's
one-time Whisper model download (free, public, no API key).

## Setup

```
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

## Run

```
venv\Scripts\python.exe flowtype.py
```

Hold **Caps Lock** (or any configured hotkey), speak, release — the
transcript is pasted at your cursor in whatever window has focus. Tap
**Esc** twice to quit.

## Installer (for a non-technical machine)

`docs/build-installer.md` builds `flowtype-setup.exe` — a per-user installer
(no admin prompt) that **bundles the `base.en` model**, so the target machine
never downloads anything. Frozen builds keep `config.json` and `logs/` in
`%APPDATA%\flowtype\` (Program Files isn't writable); `paths.py` handles the
source-vs-frozen split. End-user instructions: `docs/mum-setup.md`.

## Configuration

Settings live in `config.json`, not hardcoded constants:

```json
{
  "hotkeys": ["caps lock"],
  "model_size": "base.en",
  "max_record_seconds": 60,
  "llm_cleanup": {
    "enabled": false,
    "model": "qwen2.5:3b",
    "known_terms": ["Claude Code", "flowtype", "..."]
  }
}
```

Missing file or missing/malformed individual keys all fall back to defaults
independently — a partial config never crashes startup.

`hotkeys` accepts a list — any key in it triggers recording, so one config
can work across keyboards that don't all have the same keys. Caps Lock was
picked as the default over Right Ctrl/Right Alt (tried first, since a
laptop keyboard commonly lacks a distinct Right Ctrl) because the
`keyboard` library can't reliably tell right-side Ctrl/Alt apart from their
left-side counterparts on Windows — see `config.py`'s docstring for the
scan-code details. Caps Lock has no left/right pair to confuse it with, and
flowtype hooks it with `suppress=True` so holding it doesn't also toggle
caps state (the tradeoff: real caps-lock-toggle doesn't work while
flowtype is running).

### Optional LLM cleanup pass

Set `llm_cleanup.enabled: true` to post-process the raw Whisper transcript
through a local Ollama model (default `qwen2.5:3b`, OpenAI-compatible
endpoint at `ollama_host`) before pasting — fixes filler words/punctuation
and can correct terms in `known_terms` if Whisper mishears them.

**Honest result from testing (2026-08-04):** it reliably cleans up simple
filler words and fixed some jargon ("raton"→"ratoon", "ccs"→"CCS"), but is
**not reliable** for the specific case that motivated it — correcting
"cloud code"/"cloth code" back to "Claude Code". `qwen2.5:3b` missed it
consistently across multiple tries, and a more explicit prompt with
phonetic hints made it *worse* (substituted the wrong term entirely). This
looks like a genuine capability ceiling for a 3B model on this specific
disambiguation, not a prompt problem. Defaults to **off** — turn it on if
the general cleanup is worth the added latency (2-8s per dictation on this
model), but don't expect it to fix the Claude Code case. A bigger local
model might do better; untested.

Any failure (Ollama not running, timeout, a reply that looks unreliable —
empty, or wildly different length than the input) falls back to the raw
transcript rather than blocking dictation. Tray shows blue "✎" while this
pass runs.

## Notes

- Running from source, first run downloads the `base.en` Whisper model
  (~150MB) to the HF cache. The installer build bundles it instead.
- Clipboard is saved and restored around the paste — dictating doesn't
  destroy whatever you had copied.
- Only one instance can run at a time (Windows named mutex) — a second
  launch shows a message box and exits instead of double-pasting.
- A held hotkey auto-stops and transcribes after `max_record_seconds`
  (default 60s) so a forgotten hold can't run away with memory.
- Every transcript is appended to `logs/transcripts.jsonl` (gitignored,
  local only) — raw material for turning into SOPs later.
- Mic-open and transcription failures surface as a red "!" tray icon + a
  one-shot toast instead of failing silently.
- `bench/` benchmarks Whisper model sizes head-to-head on synthetic TTS
  audio against a known transcript — see its README-equivalent comments in
  `bench/benchmark_models.py`.

## Tests

```
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\python.exe -m pytest -v
```

Tests across `test_flowtype.py` (clipboard restore, mic-open failure,
transcription failure, double-stop safety, the watchdog, transcript
logging, the LLM cleanup on/off integration, the singleton mutex),
`test_config.py` (missing/malformed/partial config.json),
`test_paths.py` (source-vs-frozen path split, first-run config seeding), and
`test_llm_cleanup.py` (Ollama unreachable, timeout, HTTP error, unreliable
reply, malformed JSON — every failure mode falls back to the raw
transcript). Not a full suite, just what's broken or could break.

## Platform

Windows only. Hotkey capture (`keyboard`), audio (`sounddevice`), the tray
icon (`pystray`) and the clipboard paste path are all wired for Windows;
Linux/macOS would need ported equivalents.

## License

MIT
