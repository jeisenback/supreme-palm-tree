from __future__ import annotations

import os
from typing import Any, Optional

import requests


class LLMAdapter:
    """Provider interface for LLMs."""

    def summarize(self, text: str, **params: Any) -> str:
        raise NotImplementedError()

    def generate(self, prompt: str, **params: Any) -> str:
        raise NotImplementedError()


class NoOpAdapter(LLMAdapter):
    """Safe no-op adapter used when no provider key is configured.

    Returns deterministic canned responses so callers can continue without
    requiring network access.
    """

    def summarize(self, text: str, **params: Any) -> str:
        return "[LLM disabled] summary unavailable."

    def generate(self, prompt: str, **params: Any) -> str:
        return "[LLM disabled] generation unavailable."


class AnthropicAdapter(LLMAdapter):
    """Minimal Anthropic REST API adapter using `requests`.

    This adapter is intentionally small and defensive: it performs an HTTP
    POST to the Anthropic completion endpoint and returns the textual output.
    It will never raise on network/API errors — instead it returns a helpful
    error string so callers can continue.
    """

    DEFAULT_URL = "https://api.anthropic.com/v1/complete"

    def __init__(self, api_key: str, api_url: Optional[str] = None, model: str = "claude-2") -> None:
        self.api_key = api_key
        self.api_url = api_url or os.environ.get("ANTHROPIC_API_URL") or self.DEFAULT_URL
        self.model = model

    def _call_api(self, prompt: str, max_tokens: int = 512, **kwargs: Any) -> str:
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        body = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens_to_sample": int(max_tokens),
        }
        try:
            resp = requests.post(self.api_url, json=body, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            # Anthropic responses historically contain `completion` or `completion`-style fields.
            if isinstance(data, dict):
                # Common key
                for key in ("completion", "completion_text", "output", "response", "text"):
                    if key in data and isinstance(data[key], str):
                        return data[key]
                # Fallback: try nested
                if "completion" in data and isinstance(data["completion"], dict):
                    comp = data["completion"]
                    return str(comp.get("response") or comp.get("text") or comp).strip()
            return str(data)
        except Exception as e:
            return f"[anthropic-error] {e}"

    def summarize(self, text: str, **params: Any) -> str:
        prompt = f"Summarize the following text in one concise paragraph:\n\n{text}\n\nSummary:\n"
        return self._call_api(prompt, max_tokens=params.get("max_tokens", 200))

    def generate(self, prompt: str, **params: Any) -> str:
        return self._call_api(prompt, max_tokens=params.get("max_tokens", 512))


def get_adapter_from_env() -> LLMAdapter:
    """Return an adapter instance based on environment variables.

    - If `ANTHROPIC_API_KEY` is set, return `AnthropicAdapter`.
    - Otherwise return `NoOpAdapter`.
    """

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return NoOpAdapter()

    model = os.environ.get("ANTHROPIC_MODEL", "claude-2")
    api_url = os.environ.get("ANTHROPIC_API_URL")
    return AnthropicAdapter(api_key=api_key, api_url=api_url, model=model)

