from __future__ import annotations

from typing import Any, Dict, List
import re


def extract_action_items(meeting_notes: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract action items from meeting notes JSON (PoC).

    If `action_items` key exists, return it. Otherwise, do a simple
    regex-based extraction for lines that start with 'Action:' or contain
    'Action Item'. Returns list of {owner, action, due} dictionaries where
    available.
    """
    if "action_items" in meeting_notes:
        return meeting_notes["action_items"]

    text = meeting_notes.get("text", "")
    items: List[Dict[str, str]] = []
    pattern = re.compile(r"(?:Action|Action Item)[:\-]\s*(?P<action>.+?)(?:\s+\(|$)", re.I)
    for m in pattern.finditer(text):
        action = m.group("action").strip()
        # Try to find an owner (simple heuristic: look for '— Owner' or 'by NAME')
        owner_match = re.search(r"by\s+(?P<owner>[A-Z][a-zA-Z ]+)", action)
        owner = owner_match.group("owner").strip() if owner_match else ""
        due_match = re.search(r"due\s*(?P<due>\d{4}-\d{2}-\d{2})", action)
        due = due_match.group("due") if due_match else ""
        items.append({"owner": owner, "action": action, "due": due})

    return items
