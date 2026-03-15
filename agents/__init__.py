"""Agents package: lightweight adapters and role agents."""

from .llm_adapter import LLMAdapter, NoOpAdapter, get_adapter_from_env

__all__ = ["LLMAdapter", "NoOpAdapter", "get_adapter_from_env"]
