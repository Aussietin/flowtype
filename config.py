"""Loads config.json. Never crashes on a missing/malformed file — every
field falls back to its default independently, so a partial config
(e.g. just {"model_size": "small.en"}) works fine.

`hotkeys` default is ["caps lock"], not a Ctrl/Alt/Shift variant. Confirmed
2026-08-04: the `keyboard` library's Windows backend maps "right ctrl" to
scan codes (57629, 29, 57373) — scan code 29 bare, with no side/extended
info, which is also *all* of what "left ctrl" maps to. So an "on right
ctrl" hook also fires on left ctrl (same bug for right/left alt: both
share bare scan code 56). Left ctrl held briefly, e.g. during Ctrl+C,
produces a sub-0.3s clip flowtype already discards — which is why this
went unnoticed for a while. Right/left shift and right/left windows don't
have this overlap and would work, but shift is used constantly during
normal typing. Caps lock has no sided pair to be ambiguous with, and
flowtype.py hooks it with suppress=True so holding it doesn't also toggle
caps state — the tradeoff is losing the real caps-lock-toggle while
flowtype is running."""
import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


@dataclass
class LLMCleanupConfig:
    enabled: bool = False
    ollama_host: str = "http://localhost:11434"
    model: str = "qwen2.5:3b"
    timeout_seconds: float = 10.0
    known_terms: list = field(default_factory=list)


# Seed glossary — proper nouns and jargon Whisper reliably mishears. Kept
# deliberately short: `hotwords` is a decoding bias, and everyday words in
# here cause false positives (a common word forced to a rare term). Add the
# names/terms you actually dictate; don't pad it.
DEFAULT_KNOWN_TERMS = [
    "Claude Code", "flowtype", "ProjectVault", "Obsidian", "Ollama", "faster-whisper",
    "Tailscale", "WSL", "Godot", "FreeCAD", "Bambu", "NotebookLM", "T3RRA",
    "RCP", "Racecourse Projects", "Ops Center", "John Deere", "autosteer", "AB line", "RTK",
    "ratoon", "ratooning", "CCS", "billet", "headland", "fallow", "plant cane",
    "Marwood", "Blue Mountain", "Rangeview", "Clairview", "Homebush", "Mackay", "Burdekin",
    "Lili Dwyer",
]


@dataclass
class Config:
    hotkeys: list = field(default_factory=lambda: ["caps lock"])
    quit_key: str = "esc"
    model_size: str = "base.en"
    device: str = "cpu"
    compute_type: str = "int8"
    max_record_seconds: int = 60
    clipboard_restore_delay: float = 0.25
    # Transcription tuning. beam_size=1 (faster-whisper's default is 5) roughly
    # halves decode time on short dictation clips for negligible accuracy cost;
    # condition_on_previous_text=False drops the cross-segment context that
    # occasionally causes runaway repetition on a single short utterance.
    # known_terms is fed to Whisper as `hotwords` — a decoding bias toward this
    # vocabulary, at zero latency cost and no Ollama (the llm_cleanup pass tried
    # to fix the same "cloud code"->"Claude Code" class of miss, less reliably).
    beam_size: int = 1
    condition_on_previous_text: bool = False
    known_terms: list = field(default_factory=lambda: list(DEFAULT_KNOWN_TERMS))
    # Whisper strips trailing whitespace; without this, back-to-back dictations
    # collide ("...done.Next item...") and the cursor sits flush against the
    # last word every time.
    append_trailing_space: bool = True
    llm_cleanup: LLMCleanupConfig = field(default_factory=LLMCleanupConfig)


def load_config() -> Config:
    defaults = Config()
    if not CONFIG_PATH.exists():
        return defaults

    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[flowtype] config.json unreadable ({e}), using defaults")
        return defaults

    # One glossary, top-level. Falls back to a legacy llm_cleanup.known_terms
    # for configs written before it moved out, then to the built-in default.
    llm_raw = raw.get("llm_cleanup", {}) or {}
    known_terms = raw.get(
        "known_terms",
        llm_raw.get("known_terms", list(defaults.known_terms)),
    )

    llm_defaults = LLMCleanupConfig()
    llm = LLMCleanupConfig(
        enabled=llm_raw.get("enabled", llm_defaults.enabled),
        ollama_host=llm_raw.get("ollama_host", llm_defaults.ollama_host),
        model=llm_raw.get("model", llm_defaults.model),
        timeout_seconds=llm_raw.get("timeout_seconds", llm_defaults.timeout_seconds),
        known_terms=known_terms,
    )
    hotkeys = raw.get("hotkeys")
    if hotkeys is None:
        legacy_hotkey = raw.get("hotkey")
        hotkeys = [legacy_hotkey] if legacy_hotkey else defaults.hotkeys

    return Config(
        hotkeys=hotkeys,
        quit_key=raw.get("quit_key", defaults.quit_key),
        model_size=raw.get("model_size", defaults.model_size),
        device=raw.get("device", defaults.device),
        compute_type=raw.get("compute_type", defaults.compute_type),
        max_record_seconds=raw.get("max_record_seconds", defaults.max_record_seconds),
        clipboard_restore_delay=raw.get("clipboard_restore_delay", defaults.clipboard_restore_delay),
        beam_size=raw.get("beam_size", defaults.beam_size),
        condition_on_previous_text=raw.get("condition_on_previous_text", defaults.condition_on_previous_text),
        known_terms=known_terms,
        append_trailing_space=raw.get("append_trailing_space", defaults.append_trailing_space),
        llm_cleanup=llm,
    )
