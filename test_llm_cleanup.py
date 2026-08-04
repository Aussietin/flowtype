"""llm_cleanup is a best-effort enhancement — every failure mode here must
fall back to the original transcript, never raise, never block dictation."""
import requests

import llm_cleanup
from config import LLMCleanupConfig


def _cfg(**overrides):
    return LLMCleanupConfig(
        enabled=True, ollama_host="http://localhost:11434",
        model="qwen2.5:3b", timeout_seconds=5.0,
        known_terms=["Claude Code"], **overrides,
    )


class _FakeResponse:
    def __init__(self, content, status=200):
        self._content = content
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


def test_empty_input_short_circuits_without_a_network_call(monkeypatch):
    def _boom(*a, **kw):
        raise AssertionError("should not have called Ollama for empty text")
    monkeypatch.setattr(llm_cleanup.requests, "post", _boom)

    assert llm_cleanup.clean_up("   ", _cfg()) == "   "


def test_successful_cleanup_returns_model_output(monkeypatch):
    monkeypatch.setattr(llm_cleanup.requests, "post",
                         lambda *a, **kw: _FakeResponse("This is a test of local Whisper Flow, cloned for Claude Code."))

    result = llm_cleanup.clean_up("this is a test of local whisper flow cloned for cloud code", _cfg())
    assert result == "This is a test of local Whisper Flow, cloned for Claude Code."


def test_ollama_unreachable_falls_back_to_original_text(monkeypatch):
    def _boom(*a, **kw):
        raise requests.ConnectionError("no connection could be made")
    monkeypatch.setattr(llm_cleanup.requests, "post", _boom)

    original = "testing one two three"
    assert llm_cleanup.clean_up(original, _cfg()) == original


def test_timeout_falls_back_to_original_text(monkeypatch):
    def _boom(*a, **kw):
        raise requests.Timeout("timed out")
    monkeypatch.setattr(llm_cleanup.requests, "post", _boom)

    original = "testing one two three"
    assert llm_cleanup.clean_up(original, _cfg()) == original


def test_http_error_status_falls_back_to_original_text(monkeypatch):
    monkeypatch.setattr(llm_cleanup.requests, "post", lambda *a, **kw: _FakeResponse("", status=500))

    original = "testing one two three"
    assert llm_cleanup.clean_up(original, _cfg()) == original


def test_wildly_longer_reply_is_treated_as_unreliable(monkeypatch):
    """Guards against a small model 'helpfully' chatting back instead of
    just cleaning the text - a real failure mode for local models."""
    chatty = ("Sure! Here's the corrected version of your text, I've also "
              "gone ahead and fixed the grammar and added some extra "
              "context that might be helpful for you to understand: " + "word " * 50)
    monkeypatch.setattr(llm_cleanup.requests, "post", lambda *a, **kw: _FakeResponse(chatty))

    original = "testing one two three"
    assert llm_cleanup.clean_up(original, _cfg()) == original


def test_empty_reply_is_treated_as_unreliable(monkeypatch):
    monkeypatch.setattr(llm_cleanup.requests, "post", lambda *a, **kw: _FakeResponse(""))

    original = "testing one two three"
    assert llm_cleanup.clean_up(original, _cfg()) == original


def test_malformed_json_response_falls_back_to_original_text(monkeypatch):
    class _BrokenResponse:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): raise ValueError("not JSON")
    monkeypatch.setattr(llm_cleanup.requests, "post", lambda *a, **kw: _BrokenResponse())

    original = "testing one two three"
    assert llm_cleanup.clean_up(original, _cfg()) == original
