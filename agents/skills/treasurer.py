from __future__ import annotations

from typing import Dict, Any
import csv
import io


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
