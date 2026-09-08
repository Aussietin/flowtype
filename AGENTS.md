# Agent instructions — flowtype

Local hold-to-talk dictation (Wispr Flow clone, no subscription). Windows-only — hotkey,
audio, tray, and clipboard-paste are all wired for Windows.

- **Stack:** Python 3.11, faster-whisper (CTranslate2), sounddevice, keyboard, pystray,
  Pillow, tkinter (settings window). Optional local Ollama for the (default-off) cleanup pass.
- **Vault note:** `ProjectVault/01_Repositories/flowtype.md` — read it for current status,
  history, and open loops before non-trivial work. Canonical over anything stale here.
- **Runtime preflight:** `venv\Scripts\` has everything; `venv\Scripts\python.exe -m pytest`
  → 33 passing. No GPU (Intel iGPU only) — CPU int8 inference, don't add CUDA paths.
- **Config:** `config.json` (source) / `%APPDATA%\flowtype\config.json` (frozen) — `paths.py`
  owns the split. `settings_gui.py` edits it and must preserve unknown keys.
- **Installer:** `build\build.ps1` chains fetch-model → PyInstaller (`flowtype.spec`, onedir)
  → Inno Setup (`installer.iss`) → `installer-output\flowtype-setup.exe`. Not deployed; hand-carried.

## Operating contract (Claude Code + Codex)

Austin's global rules live in `~/.claude/CLAUDE.md` + `CLAUDE-shared.md` (Claude Code) and
`~/.codex/AGENTS.md` (Codex) — same contract, both agents. Load-bearing: simplest viable
solution first (no new scripts/infra unless asked), confirm the path before editing, todos are
per-project (never a global TASKS.md), commit/push only when asked and branch off the default
first, session-end `/document` capture to the vault if the work produced a decision/fix/learning.
