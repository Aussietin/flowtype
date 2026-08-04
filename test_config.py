"""config.json must never be able to crash startup — a missing, partial, or
malformed file all have to fall back to sane defaults."""
import json

import config as config_module
from config import Config, LLMCleanupConfig, load_config


def test_missing_file_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "CONFIG_PATH", tmp_path / "does_not_exist.json")
    cfg = load_config()
    assert cfg == Config()


def test_malformed_json_falls_back_to_defaults(tmp_path, monkeypatch):
    bad = tmp_path / "config.json"
    bad.write_text("{not valid json,,,", encoding="utf-8")
    monkeypatch.setattr(config_module, "CONFIG_PATH", bad)

    cfg = load_config()  # must not raise
    assert cfg == Config()


def test_partial_config_merges_with_defaults(tmp_path, monkeypatch):
    partial = tmp_path / "config.json"
    partial.write_text(json.dumps({"model_size": "small.en"}), encoding="utf-8")
    monkeypatch.setattr(config_module, "CONFIG_PATH", partial)

    cfg = load_config()
    assert cfg.model_size == "small.en"
    assert cfg.hotkeys == ["caps lock"]  # untouched default
    assert cfg.llm_cleanup == LLMCleanupConfig()  # untouched default


def test_partial_llm_cleanup_block_merges_with_defaults(tmp_path, monkeypatch):
    partial = tmp_path / "config.json"
    partial.write_text(json.dumps({"llm_cleanup": {"enabled": True}}), encoding="utf-8")
    monkeypatch.setattr(config_module, "CONFIG_PATH", partial)

    cfg = load_config()
    assert cfg.llm_cleanup.enabled is True
    assert cfg.llm_cleanup.model == "qwen2.5:3b"  # untouched default
