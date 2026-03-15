from __future__ import annotations

from typing import Dict, Any
from agents.llm_adapter import get_adapter_from_env, LLMAdapter
from agents.templating import render_template


def draft_announcement(context: Dict[str, Any], template: str | None = None, adapter: LLMAdapter | None = None) -> str:
    """Draft a short announcement for members or public channels.

    Context may include `title`, `audience`, `summary`, and `call_to_action`.
    """
    adapter = adapter or get_adapter_from_env()
    tmpl = template or (
        "# {title}\n\n{summary}\n\nAudience: {audience}\n\n{call_to_action}"
    )
    try:
        composed = render_template(tmpl, context)
    except Exception:
        composed = (
            f"{context.get('title', '')}\n\n{context.get('summary', '')}\n\n{context.get('call_to_action', '')}"
        )

    # Optionally refine with LLM
    try:
        prompt = f"Polish this announcement for clarity and brevity:\n\n{composed}"
        resp = adapter.generate(prompt)
        if isinstance(resp, str) and resp.startswith("[LLM disabled]"):
            return composed
        return resp
    except Exception:
        return composed


def generate_email_campaign(subject: str, audience_summary: str, adapter: LLMAdapter | None = None) -> Dict[str, str]:
    """Return a simple email subject + body pair (PoC), using LLM if available."""
    adapter = adapter or get_adapter_from_env()
    prompt = f"Write a short (3 paragraph) email with subject '{subject}' targeting this audience: {audience_summary}" 
    try:
        body = adapter.generate(prompt)
        if isinstance(body, str) and body.startswith("[LLM disabled]"):
            body = f"{subject}\n\nHello,\n\n{audience_summary}\n\nRegards,"
        return {"subject": subject, "body": body}
    except Exception:
        return {"subject": subject, "body": f"Hello,\n\n{audience_summary}\n\nRegards,"}
