"""settings_gui writes config.json without losing keys it doesn't manage, and
refuses to save an invalid hotkey/quit-key rather than writing junk that would
break startup.

Tk needs a display; on a machine without one the whole module skips.
"""
import importlib
import json

import pytest

tk = pytest.importorskip("tkinter")

import paths  # noqa: E402
import settings_gui  # noqa: E402


@pytest.fixture
def cfg_path(tmp_path, monkeypatch):
    p = tmp_path / "config.json"
    monkeypatch.setattr(paths, "CONFIG_PATH", p)
    monkeypatch.setattr(settings_gui, "CONFIG_PATH", p)
    return p


@pytest.fixture(scope="module")
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no Tk display available")
    root.withdraw()
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass


@pytest.fixture
def win(cfg_path, tk_root):
    container = tk.Toplevel(tk_root)
    container.withdraw()
    w = settings_gui.SettingsWindow(container)
    # never actually pop a dialog during tests
    settings_gui.messagebox.showinfo = lambda *a, **k: None
    settings_gui.messagebox.showerror = lambda *a, **k: w._errors.append(a)
    w._errors = []
    yield w
    try:
        container.destroy()
    except tk.TclError:
        pass


def test_valid_key_accepts_real_keys_rejects_junk():
    assert settings_gui._valid_key("caps lock")
    assert settings_gui._valid_key("esc")
    assert not settings_gui._valid_key("not a key")


def test_save_preserves_unknown_keys(win, cfg_path):
    win.raw = {"experimental_flag": True, "hotkey": "right ctrl"}  # + a legacy key
    win._save()
    saved = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert saved["experimental_flag"] is True
    assert "hotkey" not in saved  # legacy singular dropped
    assert saved["hotkeys"] == ["caps lock"]


def test_save_rejects_empty_hotkeys(win, cfg_path):
    win.hotkey_list.delete(0, tk.END)
    win._save()
    assert win._errors  # showerror was called
    assert not cfg_path.exists()


def test_save_rejects_bad_quit_key(win, cfg_path):
    win.quit_var.set("wingding")
    win._save()
    assert win._errors
    assert not cfg_path.exists()


def test_known_terms_roundtrip_strips_blanks(win, cfg_path):
    win.terms_text.delete("1.0", tk.END)
    win.terms_text.insert("1.0", "Claude Code\n\n  ratoon  \n\n")
    win._save()
    saved = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert saved["known_terms"] == ["Claude Code", "ratoon"]


def test_llm_block_merges_not_replaces(win, cfg_path):
    win.raw = {"llm_cleanup": {"timeout_seconds": 42, "known_terms": ["stale"]}}
    win.llm_var.set(True)
    win._sync_llm()
    win.ollama_model_var.set("qwen2.5:7b")
    win._save()
    saved = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert saved["llm_cleanup"]["timeout_seconds"] == 42  # untouched key kept
    assert saved["llm_cleanup"]["model"] == "qwen2.5:7b"
    assert saved["llm_cleanup"]["enabled"] is True
    assert "known_terms" not in saved["llm_cleanup"]  # glossary is top-level now
