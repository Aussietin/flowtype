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
import shutil
from dataclasses import dataclass, field

from paths import CONFIG_PATH, DEFAULT_CONFIG_PATH, FROZEN


@dataclass
class LLMCleanupConfig:
    enabled: bool = False
    ollama_host: str = "http://localhost:11434"
    model: str = "qwen2.5:3b"
    timeout_seconds: float = 10.0
    known_terms: list = field(default_factory=list)


@dataclass
class Config:
    hotkeys: list = field(default_factory=lambda: ["caps lock"])
    quit_key: str = "esc"
    model_size: str = "base.en"
    device: str = "cpu"
    compute_type: str = "int8"
    max_record_seconds: int = 60
    clipboard_restore_delay: float = 0.25
    llm_cleanup: LLMCleanupConfig = field(default_factory=LLMCleanupConfig)


def load_config() -> Config:
    defaults = Config()
    if not CONFIG_PATH.exists():
        # First run of an installed build: seed the user's config.json from the
        # bundled default so it's there to edit. (In a source checkout the two
        # paths are the same file, so this is skipped.)
        if FROZEN and DEFAULT_CONFIG_PATH.exists() and DEFAULT_CONFIG_PATH != CONFIG_PATH:
            try:
                shutil.copyfile(DEFAULT_CONFIG_PATH, CONFIG_PATH)
            except Exception as e:
                print(f"[flowtype] couldn't seed config.json ({e}), using defaults")
                return defaults
        else:
            return defaults

    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[flowtype] config.json unreadable ({e}), using defaults")
        return defaults

    llm_raw = raw.get("llm_cleanup", {}) or {}
    llm_defaults = LLMCleanupConfig()
    llm = LLMCleanupConfig(
        enabled=llm_raw.get("enabled", llm_defaults.enabled),
        ollama_host=llm_raw.get("ollama_host", llm_defaults.ollama_host),
        model=llm_raw.get("model", llm_defaults.model),
        timeout_seconds=llm_raw.get("timeout_seconds", llm_defaults.timeout_seconds),
        known_terms=llm_raw.get("known_terms", llm_defaults.known_terms),
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
        llm_cleanup=llm,
    )
