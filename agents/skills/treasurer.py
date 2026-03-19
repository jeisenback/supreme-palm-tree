from __future__ import annotations

from typing import Dict, Any
import csv
import io
from agents.llm_adapter import get_adapter_from_env, LLMAdapter
from agents.templating import render_template


def summarize_finances(csv_text: str) -> Dict[str, Any]:
    """Summarize simple CSV financial data (PoC).

    Expects CSV with headers: category, amount. Returns totals per category
    and a grand total.
    """
    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)
    totals: Dict[str, float] = {}
    for row in reader:
        cat = (row.get("category") or "uncategorized").strip()
        try:
            amt = float(row.get("amount") or 0)
        except ValueError:
            amt = 0.0
        totals[cat] = totals.get(cat, 0.0) + amt

    grand = sum(totals.values())
    return {"totals": totals, "grand_total": grand}


def balances_markdown(summary: Dict[str, Any]) -> str:
    lines = ["# Financial Summary", ""]
    for cat, amt in summary.get("totals", {}).items():
        lines.append(f"- **{cat}**: ${amt:,.2f}")
    lines.append("")
    lines.append(f"**Grand Total:** ${summary.get('grand_total', 0):,.2f}")
    return "\n".join(lines)


def summarize_finances_with_llm(csv_text: str, adapter: LLMAdapter | None = None, template: str | None = None) -> str:
    """Summarize finances and render a markdown using a template; uses LLM for a narrative if available.

    Falls back to `balances_markdown()` when the adapter is not available or disabled.
    """
    adapter = adapter or get_adapter_from_env()
    summary = summarize_finances(csv_text)

    # Try to produce a short narrative via LLM
    try:
        prompt = f"Summarize these financial totals: {summary}\nProvide a short paragraph." 
        narrative = adapter.summarize(prompt)
        if isinstance(narrative, str) and narrative.startswith("[LLM disabled]"):
            return balances_markdown(summary)
    except Exception:
        return balances_markdown(summary)

    # Simple rendering: include narrative then fallback to balances
    return narrative + "\n\n" + balances_markdown(summary)
