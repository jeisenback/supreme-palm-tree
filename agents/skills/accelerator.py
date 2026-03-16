from __future__ import annotations

from typing import Dict, Any
from agents.llm_adapter import get_adapter_from_env, LLMAdapter


def accelerator_program_summary(applications: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize accelerator applicants (PoC).

    Expects a mapping applicant_id -> {fields}, returns counts and top focus areas.
    """
    total = len(applications)
    focus_counts = {}
    for a in applications.values():
        focus = a.get("focus") or "general"
        focus_counts[focus] = focus_counts.get(focus, 0) + 1
    return {"total_applicants": total, "focus_counts": focus_counts}


def generate_accelerator_plan(applications: Dict[str, Any], adapter: LLMAdapter | None = None) -> str:
    adapter = adapter or get_adapter_from_env()
    summary = accelerator_program_summary(applications)
    prompt = f"Propose a 3-step plan to run an accelerator given these application stats: {summary}"
    try:
        resp = adapter.generate(prompt)
        if isinstance(resp, str) and resp.startswith("[LLM disabled]"):
            return "1. Select top applicants\n2. Pair mentors\n3. Host kickoff and demo day"
        return resp
    except Exception:
        return "1. Select top applicants\n2. Pair mentors\n3. Host kickoff and demo day"
