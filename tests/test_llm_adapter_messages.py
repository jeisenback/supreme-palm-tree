"""Tests for agents/llm_adapter.py — AnthropicMessagesAdapter and factory."""

import sys
from pathlib import Path

import pytest
import responses as rsps_lib  # `responses` library for mocking requests

# agents/ is not on sys.path by default in tests — add it
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "agents"))

from llm_adapter import (
    AnthropicMessagesAdapter,
    APIKeyError,
    ContentGenerationError,
    LLMAdapter,
    NoOpAdapter,
    generate_content_draft,
    get_adapter_from_env,
    _MESSAGES_URL,
)


# ---------------------------------------------------------------------------
# NoOpAdapter
# ---------------------------------------------------------------------------

def test_noop_summarize_returns_string():
    adapter = NoOpAdapter()
    result = adapter.summarize("some text")
    assert isinstance(result, str)
    assert len(result) > 0


def test_noop_generate_returns_string():
    adapter = NoOpAdapter()
    result = adapter.generate("some prompt")
    assert isinstance(result, str)
    assert len(result) > 0


def test_noop_is_llm_adapter_subclass():
    assert isinstance(NoOpAdapter(), LLMAdapter)


# ---------------------------------------------------------------------------
# get_adapter_from_env
# ---------------------------------------------------------------------------

def test_no_env_key_returns_noop(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    adapter = get_adapter_from_env()
    assert isinstance(adapter, NoOpAdapter)


def test_env_key_present_returns_messages_adapter(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-123")
    adapter = get_adapter_from_env()
    assert isinstance(adapter, AnthropicMessagesAdapter)


def test_env_model_override(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-123")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4-6")
    adapter = get_adapter_from_env()
    assert isinstance(adapter, AnthropicMessagesAdapter)
    assert adapter.model == "claude-opus-4-6"


# ---------------------------------------------------------------------------
# AnthropicMessagesAdapter — _call_messages (mocked HTTP)
# ---------------------------------------------------------------------------

def _mock_200_body(text: str) -> dict:
    return {
        "id": "msg_123",
        "type": "message",
        "content": [{"type": "text", "text": text}],
        "model": "claude-haiku-4-5-20251001",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }


@rsps_lib.activate
def test_call_messages_returns_text():
    rsps_lib.add(rsps_lib.POST, _MESSAGES_URL, json=_mock_200_body("Hello, world!"), status=200)
    adapter = AnthropicMessagesAdapter(api_key="test-key")
    result = adapter._call_messages("Greet me")
    assert result == "Hello, world!"


@rsps_lib.activate
def test_call_messages_uses_system_message():
    """Verify system field is included when system_message is provided."""
    captured = {}

    def callback(request):
        import json as _json
        body = _json.loads(request.body)
        captured["has_system"] = "system" in body
        captured["system"] = body.get("system", "")
        return (200, {}, _json.dumps(_mock_200_body("ok")))

    rsps_lib.add_callback(rsps_lib.POST, _MESSAGES_URL, callback=callback,
                          content_type="application/json")
    adapter = AnthropicMessagesAdapter(api_key="test-key")
    adapter._call_messages("user msg", system_message="Be concise.")
    assert captured["has_system"] is True
    assert captured["system"] == "Be concise."


@rsps_lib.activate
def test_call_messages_no_system_when_empty():
    """Verify system field is omitted when system_message is empty."""
    captured = {}

    def callback(request):
        import json as _json
        body = _json.loads(request.body)
        captured["has_system"] = "system" in body
        return (200, {}, _json.dumps(_mock_200_body("ok")))

    rsps_lib.add_callback(rsps_lib.POST, _MESSAGES_URL, callback=callback,
                          content_type="application/json")
    adapter = AnthropicMessagesAdapter(api_key="test-key")
    adapter._call_messages("user msg", system_message="")
    assert captured["has_system"] is False


@rsps_lib.activate
def test_call_messages_raises_on_http_error():
    rsps_lib.add(rsps_lib.POST, _MESSAGES_URL, status=401,
                 json={"error": {"type": "authentication_error"}})
    adapter = AnthropicMessagesAdapter(api_key="bad-key")
    with pytest.raises(ContentGenerationError):
        adapter._call_messages("prompt")


@rsps_lib.activate
def test_call_messages_raises_on_empty_content():
    """Empty content-blocks list → ContentGenerationError."""
    rsps_lib.add(rsps_lib.POST, _MESSAGES_URL, json={
        "content": [],
        "stop_reason": "end_turn",
    }, status=200)
    adapter = AnthropicMessagesAdapter(api_key="test-key")
    with pytest.raises(ContentGenerationError, match="empty"):
        adapter._call_messages("prompt")


@rsps_lib.activate
def test_call_messages_handles_multiple_text_blocks():
    """Multiple text blocks should be joined with newlines."""
    body = {
        "content": [
            {"type": "text", "text": "First part."},
            {"type": "text", "text": "Second part."},
        ],
    }
    rsps_lib.add(rsps_lib.POST, _MESSAGES_URL, json=body, status=200)
    adapter = AnthropicMessagesAdapter(api_key="test-key")
    result = adapter._call_messages("prompt")
    assert "First part." in result
    assert "Second part." in result


@rsps_lib.activate
def test_generate_returns_text():
    rsps_lib.add(rsps_lib.POST, _MESSAGES_URL, json=_mock_200_body("Generated content."), status=200)
    adapter = AnthropicMessagesAdapter(api_key="test-key")
    result = adapter.generate("Write something")
    assert result == "Generated content."


@rsps_lib.activate
def test_generate_on_api_error_returns_error_string():
    """generate() catches ContentGenerationError and returns error string."""
    rsps_lib.add(rsps_lib.POST, _MESSAGES_URL, status=500, json={"error": "server error"})
    adapter = AnthropicMessagesAdapter(api_key="test-key")
    result = adapter.generate("prompt")
    assert result.startswith("[anthropic-error]")


@rsps_lib.activate
def test_summarize_returns_text():
    rsps_lib.add(rsps_lib.POST, _MESSAGES_URL, json=_mock_200_body("A brief summary."), status=200)
    adapter = AnthropicMessagesAdapter(api_key="test-key")
    result = adapter.summarize("Long text to summarize.")
    assert result == "A brief summary."


# ---------------------------------------------------------------------------
# generate_content_draft
# ---------------------------------------------------------------------------

def test_generate_content_draft_raises_api_key_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(APIKeyError):
        generate_content_draft("ecba_session", "slides", {})


@rsps_lib.activate
def test_generate_content_draft_returns_string(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-123")
    rsps_lib.add(
        rsps_lib.POST, _MESSAGES_URL,
        json=_mock_200_body("## Learning Objective\nBy the end...\n## Slide 1\n- Point A\n---"),
        status=200,
    )
    result = generate_content_draft("ecba_session", "slides", {"topic": "BACCM"})
    assert isinstance(result, str)
    assert len(result) > 0


@rsps_lib.activate
def test_generate_content_draft_includes_slot_prompt(monkeypatch):
    """The user message sent to the API should mention the slot instruction."""
    captured = {}

    def callback(request):
        import json as _json
        body = _json.loads(request.body)
        captured["user_message"] = body["messages"][0]["content"]
        return (200, {}, _json.dumps(_mock_200_body("ok slide deck")))

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    rsps_lib.add_callback(rsps_lib.POST, _MESSAGES_URL, callback=callback,
                          content_type="application/json")
    generate_content_draft("ecba_session", "slides", {})
    assert "slide" in captured["user_message"].lower()
