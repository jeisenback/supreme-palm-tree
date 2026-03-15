from __future__ import annotations

import os
from typing import Any


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


def get_adapter_from_env() -> LLMAdapter:
    """Return an adapter instance based on environment variables.

    For now this returns `NoOpAdapter` when `ANTHROPIC_API_KEY` is not set.
    Future implementations should detect provider and return a real adapter.
    """

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return NoOpAdapter()

    # Placeholder: real Anthropic adapter not implemented in PoC.
    return NoOpAdapter()
