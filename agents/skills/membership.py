from __future__ import annotations

from typing import Dict, Any
from agents.llm_adapter import get_adapter_from_env, LLMAdapter


def analyze_membership(csv_text: str) -> Dict[str, Any]:
    """Simple membership trend analyzer PoC.

Expects CSV with headers: member_id, joined_date, status (active|lapsed)
Returns counts and churn estimate.
"""
    import io
    import csv
    from collections import Counter

    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)
    statuses = Counter()
    for row in reader:
        st = (row.get("status") or "active").strip().lower()
        statuses[st] += 1

    total = sum(statuses.values())
    active = statuses.get("active", 0)
    lapsed = statuses.get("lapsed", 0)
    churn = (lapsed / total) if total else 0.0
    return {"total": total, "active": active, "lapsed": lapsed, "churn_rate": churn}


def membership_summary_markdown(summary: Dict[str, Any]) -> str:
    lines = ["# Membership Summary", ""]
    lines.append(f"- Total members: {summary.get('total', 0)}")
    lines.append(f"- Active: {summary.get('active', 0)}")
    lines.append(f"- Lapsed: {summary.get('lapsed', 0)}")
    lines.append(f"- Estimated churn rate: {summary.get('churn_rate', 0):.2%}")
    return "\n".join(lines)


def generate_membership_insights(csv_text: str, adapter: LLMAdapter | None = None) -> str:
    adapter = adapter or get_adapter_from_env()
    summary = analyze_membership(csv_text)
    try:
        prompt = f"Provide 3 actionable suggestions to reduce churn given these metrics: {summary}"
        resp = adapter.summarize(prompt)
        if isinstance(resp, str) and resp.startswith("[LLM disabled]"):
            return membership_summary_markdown(summary)
        return resp + "\n\n" + membership_summary_markdown(summary)
    except Exception:
        return membership_summary_markdown(summary)
