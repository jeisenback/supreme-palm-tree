from __future__ import annotations

from typing import Dict, Any
from agents.llm_adapter import get_adapter_from_env, LLMAdapter


def suggest_training_programs(member_skills: Dict[str, int]) -> Dict[str, Any]:
    """Given a mapping of skill -> count/level, suggest training focus areas.

    member_skills is a PoC structure mapping skill names to numeric counts or levels.
    """
    # simple heuristic: pick top 3 skills with lowest average level
    if not member_skills:
        return {"recommendations": []}

    sorted_skills = sorted(member_skills.items(), key=lambda kv: kv[1])
    recs = [s for s, _ in sorted_skills[:3]]
    return {"recommendations": recs, "summary": {k: v for k, v in member_skills.items()}}


def generate_profdev_plan(member_skills: Dict[str, int], adapter: LLMAdapter | None = None) -> str:
    """Create a short professional development plan. Uses LLM when available."""
    adapter = adapter or get_adapter_from_env()
    summary = suggest_training_programs(member_skills)
    prompt = f"Generate a 3-point professional development plan based on these member skill levels: {summary}"
    try:
        resp = adapter.generate(prompt)
        if isinstance(resp, str) and resp.startswith("[LLM disabled]"):
            return "\n".join([f"- {r}" for r in summary.get("recommendations", [])])
        return resp
    except Exception:
        return "\n".join([f"- {r}" for r in summary.get("recommendations", [])])
