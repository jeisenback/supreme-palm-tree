from __future__ import annotations

from typing import Any, Mapping


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:  # pragma: no cover - trivial
        return ""


def render_template(template: str, context: Mapping[str, Any]) -> str:
    """Render a very small, safe template using `str.format_map`.

    This PoC avoids external dependencies. Missing keys are replaced with
    empty strings so templates are forgiving.
    """
    return template.format_map(_SafeDict(context))
