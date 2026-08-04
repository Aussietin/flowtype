"""Loads config.json. Never crashes on a missing/malformed file — every
field falls back to its default independently, so a partial config
(e.g. just {"model_size": "small.en"}) works fine."""
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


@dataclass
class Config:
    hotkeys: list = field(default_factory=lambda: ["right ctrl"])
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
