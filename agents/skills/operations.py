from __future__ import annotations

from typing import Dict, Any
from agents.llm_adapter import get_adapter_from_env, LLMAdapter


def operations_checklist(context: Dict[str, Any]) -> Dict[str, Any]:
    """Return an operations readiness checklist based on provided context.

    Context may include keys: `facilities`, `compliance`, `finance_controls`.
    This is a PoC heuristic-based checklist generator.
    """
    checklist = []
    if not context.get("facilities"):
        checklist.append("Review facilities and equipment status")
    if not context.get("compliance"):
        checklist.append("Confirm compliance filings are up to date")
    if not context.get("finance_controls"):
        checklist.append("Validate finance controls and signatory lists")
    if not checklist:
        checklist.append("Operations appear in good standing; schedule routine review")
    return {"checklist": checklist}


def generate_ops_plan(context: Dict[str, Any], adapter: LLMAdapter | None = None) -> str:
    adapter = adapter or get_adapter_from_env()
    summary = operations_checklist(context)
    prompt = f"Create a short operations action plan based on these items: {summary['checklist']}"
    try:
        resp = adapter.generate(prompt)
        if isinstance(resp, str) and resp.startswith("[LLM disabled]"):
            return "\n".join([f"- {s}" for s in summary["checklist"]])
        return resp
    except Exception:
        return "\n".join([f"- {s}" for s in summary["checklist"]])
