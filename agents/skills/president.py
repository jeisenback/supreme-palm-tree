from __future__ import annotations

from typing import Any, Dict
from agents.llm_adapter import get_adapter_from_env, LLMAdapter
from agents.templating import render_template


def generate_agenda(meeting_notes: Dict[str, Any]) -> str:
    """Generate a simple agenda markdown from meeting notes JSON (PoC).

    Expects keys like `title`, `date`, `summary`, and optional `topics`.
    """
    title = meeting_notes.get("title", "Board Meeting")
    date = meeting_notes.get("date", "TBD")
    summary = meeting_notes.get("summary", "")
    topics = meeting_notes.get("topics") or []

    md_lines = [f"# Agenda — {title}", f"**Date:** {date}", ""]
    if summary:
        md_lines += ["## Meeting Brief", summary, ""]

    md_lines.append("## Proposed Agenda")
    if topics:
        for i, t in enumerate(topics, start=1):
            md_lines.append(f"{i}. {t}")
    else:
        md_lines += [
            "1. Call to Order",
            "2. Approval of Minutes",
            "3. Officer Reports",
            "4. Committee Updates",
            "5. New Business",
            "6. Review Action Items",
            "7. Adjourn",
        ]

    return "\n".join(md_lines)


def generate_agenda_with_llm(meeting_notes: Dict[str, Any], adapter: LLMAdapter | None = None, template: str | None = None) -> str:
    """Generate an agenda using the LLM adapter and a template if available.

    If `adapter` is not provided, `get_adapter_from_env()` is used. When the
    adapter indicates LLM is disabled, this function falls back to the
    deterministic `generate_agenda()` implementation.
    """
    adapter = adapter or get_adapter_from_env()
    # Try to summarize the meeting brief if present
    summary = meeting_notes.get("summary", "")
    llm_summary = ""
    try:
        llm_summary = adapter.summarize(summary or "")
    except Exception:
        llm_summary = ""

    # If adapter is the NoOp (returns disabled message), fallback
    if isinstance(llm_summary, str) and llm_summary.startswith("[LLM disabled]"):
        return generate_agenda(meeting_notes)

    context = {
        "title": meeting_notes.get("title", "Board Meeting"),
        "date": meeting_notes.get("date", "TBD"),
        "summary": llm_summary or summary,
        "topics": "\n".join(meeting_notes.get("topics", [])) if meeting_notes.get("topics") else "",
    }

    tmpl = template or (
        "# Agenda — {title}\n**Date:** {date}\n\n## Meeting Brief\n{summary}\n\n## Proposed Agenda\n{topics}"
    )
    return render_template(tmpl, context)
