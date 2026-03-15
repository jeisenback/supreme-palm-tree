"""Process meeting transcripts into notes, action items, and research items.

Lightweight heuristics are used to extract action and research items. When an
LLM adapter is available it will be used to generate a concise meeting
summary; otherwise a simple fallback summary is produced.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict, Optional

try:
    from agents.llm_adapter import LLMAdapter
except Exception:
    LLMAdapter = None


ACTION_RE = re.compile(r"(?im)^\s*(?:action|action item|todo|to do)[:\-\s]*(.+)$")
TASK_RE = re.compile(r"(?m)^\s*- \[ \] (.+)$")
RESEARCH_RE = re.compile(r"(?im)^\s*(?:research|investigate|follow up|follow-up)[:\-\s]*(.+)$")


def parse_transcript_text(text: str, use_llm: bool = True) -> Dict[str, List[str]]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Extract action items heuristically
    actions = []
    for m in ACTION_RE.finditer(text):
        actions.append(m.group(1).strip())
    for m in TASK_RE.finditer(text):
        actions.append(m.group(1).strip())

    # Extract research/follow-up items
    research = []
    for m in RESEARCH_RE.finditer(text):
        research.append(m.group(1).strip())

    # Fallback: look for lines containing 'follow up' or 'investigate'
    for i, l in enumerate(lines):
        if re.search(r"follow up|follow-up|investigate", l, flags=re.I):
            research.append(l)

    # Compose meeting notes: prefer LLM if available
    notes = []
    if use_llm and LLMAdapter is not None:
        try:
            adapter = LLMAdapter()
            summary = adapter.summarize("\n".join(lines))
            notes = [summary]
        except Exception:
            notes = ["\n".join(lines[:20])]
    else:
        notes = ["\n".join(lines[:20])]

    return {"notes": notes, "action_items": actions, "research_items": research}


def process_transcript_file(path: str, out_dir: str = "out/transcripts", use_llm: bool = True) -> Path:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore")
    parsed = parse_transcript_text(text, use_llm=use_llm)

    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    dest = outp / (p.stem + ".processed.md")

    parts = [f"# Meeting Notes: {p.name}\n"]
    parts.append("## Summary\n")
    parts.extend([f"{s}\n" for s in parsed["notes"]])

    parts.append("\n## Action Items\n")
    if parsed["action_items"]:
        for a in parsed["action_items"]:
            parts.append(f"- {a}\n")
    else:
        parts.append("_No explicit action items found._\n")

    parts.append("\n## Research / Follow-ups\n")
    if parsed["research_items"]:
        for r in parsed["research_items"]:
            parts.append(f"- {r}\n")
    else:
        parts.append("_No research items found._\n")

    dest.write_text("\n".join(parts), encoding="utf-8")
    # Wire action items into tasks and schedule reminders
    try:
        from agents import tasks as _tasks
        from agents import scheduler as _scheduler

        for ai in parsed.get("action_items", []):
            t = _tasks.add_task(title=ai if len(ai) < 120 else ai[:120], description=ai, due_days=7)
            # schedule a one-off reminder in 7 days (604800 seconds)
            try:
                job_name = f"reminder-{t['id']}"
                def _make_reminder(task_id: str, title: str):
                    def _remind():
                        print(f"Reminder for task {task_id}: {title}")
                    return _remind

                _scheduler.schedule_one_off(job_name, _make_reminder(t["id"], t["title"]), delay_seconds=7 * 24 * 60 * 60)
            except Exception:
                pass
    except Exception:
        # best-effort wiring; if tasks or scheduler are unavailable, skip
        pass
    return dest
