from __future__ import annotations

from typing import Dict, Any
from agents.llm_adapter import get_adapter_from_env, LLMAdapter
from agents.templating import render_template


def summarize_donors(csv_text: str) -> Dict[str, Any]:
    """Simple CSV donor summary PoC.

    Expects CSV with headers: donor, amount, email (optional).
    Returns totals and top donors.
    """
    import io
    import csv

    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)
    totals: Dict[str, float] = {}
    donors: Dict[str, float] = {}
    for row in reader:
        name = (row.get("donor") or "anonymous").strip()
        try:
            amt = float(row.get("amount") or 0)
        except ValueError:
            amt = 0.0
        donors[name] = donors.get(name, 0.0) + amt
    grand = sum(donors.values())
    top = sorted(donors.items(), key=lambda x: x[1], reverse=True)[:5]
    return {"grand_total": grand, "top_donors": top, "donor_count": len(donors)}


def fundraising_plan_prompt(summary: Dict[str, Any]) -> str:
    return (
        "Based on these donor statistics, propose a 3-point fundraising plan aimed at increasing recurring donations:\n"
        f"Summary: {summary}"
    )


def generate_fundraising_plan(csv_text: str, adapter: LLMAdapter | None = None, template: str | None = None) -> str:
    """Return a short fundraising plan; uses LLM when available, else a deterministic fallback."""
    adapter = adapter or get_adapter_from_env()
    summary = summarize_donors(csv_text)
    prompt = fundraising_plan_prompt(summary)
    try:
        resp = adapter.generate(prompt)
        if isinstance(resp, str) and resp.startswith("[LLM disabled]"):
            # Fallback plan
            lines = ["1. Reach out to top donors for recurring gifts.", "2. Launch a membership-level recurring program.", "3. Host a small donor appreciation event."]
            return "\n".join(lines)
        return resp
    except Exception:
        lines = [
            "1. Reach out to top donors for recurring gifts.",
            "2. Launch a membership-level recurring program.",
            "3. Host a small donor appreciation event.",
        ]
        return "\n".join(lines)
