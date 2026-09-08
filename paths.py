"""Path resolution — works both from source and from a PyInstaller freeze.

From source (dev): everything lives next to this file in the repo.

Frozen (installed via flowtype-setup.exe): read-only bundled assets live under
``sys._MEIPASS`` (PyInstaller's ``_internal`` dir); anything writable — config.json
and the transcript log — must go to ``%APPDATA%\\flowtype`` because Program Files
is not writable for a normal user.
"""
import os
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)

# Directory holding read-only bundled resources (default config, whisper model).
if FROZEN:
    BUNDLE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    BUNDLE_DIR = Path(__file__).resolve().parent

# Directory for user-writable state (config.json, logs/).
if FROZEN:
    USER_DIR = Path(os.environ.get("APPDATA", Path.home())) / "flowtype"
else:
    USER_DIR = Path(__file__).resolve().parent

USER_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = USER_DIR / "config.json"
DEFAULT_CONFIG_PATH = BUNDLE_DIR / "config.json"
TRANSCRIPT_LOG = USER_DIR / "logs" / "transcripts.jsonl"

# A bundled CT2 whisper model dir (populated by build/fetch_model.py before the
# freeze). When present, WhisperModel loads it directly instead of hitting the
# Hugging Face Hub — a non-technical user must never see a first-run download.
_bundled_model = BUNDLE_DIR / "models" / "base.en"
MODEL_DIR = _bundled_model if (_bundled_model / "model.bin").exists() else None
