# Building `flowtype-setup.exe`

A repeatable Windows build. Produces a per-user installer (~200 MB) that bundles
the `base.en` whisper model so the target machine never downloads anything.

## One-time setup

```powershell
winget install JRSoftware.InnoSetup      # provides iscc.exe
venv\Scripts\python.exe -m pip install pyinstaller pyinstaller-hooks-contrib
```

## Build

```powershell
# 1. fetch the model (once; ~145 MB into build/model/, gitignored)
venv\Scripts\python.exe build\fetch_model.py

# 2. freeze — onedir tree at build/dist/flowtype/
venv\Scripts\pyinstaller flowtype.spec --noconfirm --distpath build\dist --workpath build\work

# 3. installer — installer-output/flowtype-setup.exe
iscc installer.iss
```

Or run `build\build.ps1` which chains all three.

## What the freeze changes vs a source run

- `paths.py` detects `sys.frozen`. Bundled read-only assets (default `config.json`,
  the model) resolve under `sys._MEIPASS`; writable state (`config.json`, `logs/`)
  goes to `%APPDATA%\flowtype\`.
- First launch seeds `%APPDATA%\flowtype\config.json` from the bundled default.
- `flowtype.py` loads the model from the bundled `models/base.en/` dir instead of
  the Hugging Face cache.

## Verifying a build

On a clean Windows account (or VM):

1. Run `flowtype-setup.exe` — no UAC prompt (per-user).
2. Start Menu → flowtype → launches, tray shows the grey diamond.
3. Hold Right Ctrl, speak, release → text pastes at the cursor.
4. Deny microphone access once → red "!" tray icon + toast (not a silent failure).
5. `%APPDATA%\flowtype\config.json` and `logs\transcripts.jsonl` exist and are written.
6. Uninstall → Start Menu entry, install dir, and the logs dir are gone.

## Notes

- **Unsigned.** SmartScreen shows "Windows protected your PC" → *More info → Run
  anyway*. No code-signing cert. Covered for the recipient in `docs/mum-setup.md`.
- `base.en` only. `small.en` was benchmarked (2026-08-04) with no accuracy win.
- LLM cleanup ships **off** — no Ollama dependency in the freeze.
