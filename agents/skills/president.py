from __future__ import annotations

from typing import Any, Dict


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
