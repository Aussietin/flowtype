"""paths.py resolution + first-run config seeding for a frozen build.

These tests reload `paths` and `config` under a faked frozen environment, so a
fixture restores both modules to their normal (source) state afterwards.
"""
import importlib
import json
import sys

import pytest


@pytest.fixture(autouse=True)
def restore_modules():
    yield
    import paths
    importlib.reload(paths)
    import config
    importlib.reload(config)


def _reload_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    (tmp_path / "bundle").mkdir(parents=True, exist_ok=True)
    import paths
    return importlib.reload(paths)


def test_source_layout_keeps_everything_in_repo():
    import paths
    p = importlib.reload(paths)
    assert p.FROZEN is False
    assert p.CONFIG_PATH == p.DEFAULT_CONFIG_PATH
    assert p.USER_DIR == p.BUNDLE_DIR


def test_frozen_layout_splits_bundle_from_user_dir(monkeypatch, tmp_path):
    p = _reload_frozen(monkeypatch, tmp_path)
    assert p.FROZEN is True
    assert p.BUNDLE_DIR == (tmp_path / "bundle")
    assert p.USER_DIR == (tmp_path / "appdata" / "flowtype")
    assert p.USER_DIR.is_dir()
    assert p.CONFIG_PATH != p.DEFAULT_CONFIG_PATH


def test_frozen_first_run_seeds_config_from_bundled_default(monkeypatch, tmp_path):
    p = _reload_frozen(monkeypatch, tmp_path)
    p.DEFAULT_CONFIG_PATH.write_text(
        json.dumps({"model_size": "base.en", "hotkeys": ["right ctrl"]}), encoding="utf-8"
    )
    import config
    importlib.reload(config)

    assert not p.CONFIG_PATH.exists()
    cfg = config.load_config()

    assert p.CONFIG_PATH.exists()  # seeded from the bundled default
    assert cfg.hotkeys == ["right ctrl"]
