"""
Targeted tests for the robustness fixes: clipboard preservation, mic-open
failure, transcription failure, double-stop safety, the max-duration
watchdog, and the single-instance mutex. Not a full suite — just the things
that broke or could break, found by reading the code adversarially.

Run: venv\\Scripts\\python.exe -m pytest test_flowtype.py -v
"""
import ctypes
import json
import threading
import time

import numpy as np
import pytest

import flowtype


@pytest.fixture(autouse=True)
def reset_state():
    flowtype._recording = False
    flowtype._frames = []
    flowtype._stream = None
    flowtype._status = "idle"
    flowtype._error = None
    yield
    flowtype._recording = False
    flowtype._frames = []
    flowtype._stream = None
    flowtype._status = "idle"
    flowtype._error = None


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeModel:
    def __init__(self, text=""):
        self._text = text

    def transcribe(self, audio, language="en", vad_filter=True):
        if self._text:
            return [FakeSegment(self._text)], None
        return [], None


def test_clipboard_save_and_restore(monkeypatch):
    """Dictating must not permanently destroy whatever was on the clipboard."""
    sent = []
    monkeypatch.setattr(flowtype.keyboard, "send", lambda combo: sent.append(combo))

    real_original = flowtype.pyperclip.paste()  # whatever was really there
    try:
        flowtype.pyperclip.copy("pre-existing clipboard content")

        flowtype._paste("dictated text")

        assert flowtype.pyperclip.paste() == "dictated text"
        assert sent == ["ctrl+v"]

        time.sleep(flowtype.CFG.clipboard_restore_delay + 0.3)
        assert flowtype.pyperclip.paste() == "pre-existing clipboard content"
    finally:
        flowtype.pyperclip.copy(real_original)


def test_mic_open_failure_reports_error_and_does_not_stick(monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("no such device")
    monkeypatch.setattr(flowtype.sd, "InputStream", _boom)

    flowtype.start_recording(FakeModel())

    assert flowtype._recording is False
    assert flowtype._status == "idle"

    state = flowtype.poll()
    assert state.color == flowtype.RED
    assert "no such device" in state.tooltip
    assert state.notify is not None

    state2 = flowtype.poll()  # error is one-shot
    assert state2.color == flowtype.GREY


def test_transcription_failure_reports_error_and_resets_status():
    class BoomModel:
        def transcribe(self, audio, language="en", vad_filter=True):
            raise RuntimeError("ctranslate2 exploded")

    flowtype._recording = True
    flowtype._frames = [np.zeros((16000, 1), dtype=np.float32)]  # 1s, clears the 0.3s floor

    flowtype.stop_recording_and_transcribe(BoomModel())

    assert flowtype._status == "idle"
    state = flowtype.poll()
    assert state.color == flowtype.RED
    assert "ctranslate2 exploded" in state.tooltip


def test_double_stop_only_transcribes_once():
    class TrackingModel:
        calls = 0

        def transcribe(self, audio, language="en", vad_filter=True):
            TrackingModel.calls += 1
            return [], None

    flowtype._recording = True
    flowtype._frames = [np.zeros((16000, 1), dtype=np.float32)]

    t1 = threading.Thread(target=flowtype.stop_recording_and_transcribe, args=(TrackingModel(),))
    t2 = threading.Thread(target=flowtype.stop_recording_and_transcribe, args=(TrackingModel(),))
    t1.start(); t1.join()
    t2.start(); t2.join()

    assert TrackingModel.calls == 1


def test_watchdog_auto_stops_a_forgotten_hold(monkeypatch):
    monkeypatch.setattr(flowtype.CFG, "max_record_seconds", 1)
    monkeypatch.setattr(flowtype.keyboard, "send", lambda combo: None)

    flowtype.start_recording(FakeModel())
    assert flowtype._status == "recording"

    time.sleep(1.6)
    assert flowtype._status == "idle"
    assert flowtype._recording is False


def test_transcript_gets_logged(tmp_path, monkeypatch):
    log_path = tmp_path / "transcripts.jsonl"
    monkeypatch.setattr(flowtype, "TRANSCRIPT_LOG", log_path)
    monkeypatch.setattr(flowtype.keyboard, "send", lambda combo: None)
    monkeypatch.setattr(flowtype.pyperclip, "copy", lambda t: None)
    monkeypatch.setattr(flowtype.pyperclip, "paste", lambda: "unrelated clipboard content")

    flowtype._recording = True
    flowtype._frames = [np.zeros((16000, 1), dtype=np.float32)]
    flowtype.stop_recording_and_transcribe(FakeModel(text="testing one two three"))

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["text"] == "testing one two three"
    assert "ts" in entry


def test_llm_cleanup_runs_when_enabled_and_status_shows_cleaning(monkeypatch):
    # Mock pyperclip entirely rather than touching the real clipboard — the
    # background restore thread from _paste() outlives a single test and was
    # racing with other tests' clipboard assertions in the same run.
    copied = []
    monkeypatch.setattr(flowtype.pyperclip, "copy", lambda t: copied.append(t))
    monkeypatch.setattr(flowtype.pyperclip, "paste", lambda: "unrelated clipboard content")
    monkeypatch.setattr(flowtype.CFG.llm_cleanup, "enabled", True)
    monkeypatch.setattr(flowtype.keyboard, "send", lambda combo: None)

    seen_status_during_cleanup = []

    def _fake_clean_up(text, cfg):
        seen_status_during_cleanup.append(flowtype._status)
        return text.upper()

    monkeypatch.setattr(flowtype.llm_cleanup, "clean_up", _fake_clean_up)

    flowtype._recording = True
    flowtype._frames = [np.zeros((16000, 1), dtype=np.float32)]
    flowtype.stop_recording_and_transcribe(FakeModel(text="lower case text"))

    assert seen_status_during_cleanup == ["cleaning"]
    assert copied[0] == "LOWER CASE TEXT"


def test_llm_cleanup_skipped_when_disabled(monkeypatch):
    copied = []
    monkeypatch.setattr(flowtype.pyperclip, "copy", lambda t: copied.append(t))
    monkeypatch.setattr(flowtype.pyperclip, "paste", lambda: "unrelated clipboard content")
    monkeypatch.setattr(flowtype.CFG.llm_cleanup, "enabled", False)
    monkeypatch.setattr(flowtype.keyboard, "send", lambda combo: None)

    def _should_not_be_called(text, cfg):
        raise AssertionError("clean_up should not run when disabled")
    monkeypatch.setattr(flowtype.llm_cleanup, "clean_up", _should_not_be_called)

    flowtype._recording = True
    flowtype._frames = [np.zeros((16000, 1), dtype=np.float32)]
    flowtype.stop_recording_and_transcribe(FakeModel(text="raw text"))

    assert copied[0] == "raw text"


def test_singleton_mutex_detects_second_instance():
    kernel32 = ctypes.windll.kernel32
    ERROR_ALREADY_EXISTS = 183
    name = "Global\\flowtype_singleton_test"

    h1 = kernel32.CreateMutexW(None, False, name)
    assert kernel32.GetLastError() != ERROR_ALREADY_EXISTS

    h2 = kernel32.CreateMutexW(None, False, name)
    assert kernel32.GetLastError() == ERROR_ALREADY_EXISTS

    kernel32.CloseHandle(h1)
    kernel32.CloseHandle(h2)
