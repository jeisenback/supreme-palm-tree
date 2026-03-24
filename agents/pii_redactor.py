from __future__ import annotations

import re
from typing import Any


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b")


def redact_text(text: str) -> str:
    """Redact common PII from a text string (emails, US-style phones).

    This is intentionally conservative and simplistic for PoC use.
    """
    if not isinstance(text, str):
        return text
    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = PHONE_RE.sub("[REDACTED_PHONE]", text)
    return text


def redact_context(obj: Any) -> Any:
    """Walk a JSON-like structure and redact text fields in-place (returns new structure).

    - Strings get redacted via `redact_text`.
    - Lists and dicts are processed recursively.
    - Other values are returned unchanged.
    """
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {k: redact_context(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_context(v) for v in obj]
    return obj
