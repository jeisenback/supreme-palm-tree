from __future__ import annotations

from typing import Any, Dict, List
import re
from agents.llm_adapter import get_adapter_from_env, LLMAdapter


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


def extract_action_items_with_llm(meeting_notes: Dict[str, Any], adapter: LLMAdapter | None = None) -> List[Dict[str, str]]:
    """Attempt to use the LLM to extract action items; fall back to regex extractor.

    Uses `adapter.generate()` to ask the model to return JSON action items. If
    the adapter is a NoOp or returns a disabled message, this will fall back
    to `extract_action_items()`.
    """
    adapter = adapter or get_adapter_from_env()
    text = meeting_notes.get("text", "")
    try:
        prompt = f"Extract action items from the following notes. Return as JSON list of {{owner, action, due}}:\n\n{text}"
        resp = adapter.generate(prompt)
        if isinstance(resp, str) and resp.startswith("[LLM disabled]"):
            return extract_action_items(meeting_notes)
        # Best-effort: try to parse a JSON-like response; otherwise fallback
        import json

        try:
            parsed = json.loads(resp)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return extract_action_items(meeting_notes)
    except Exception:
        return extract_action_items(meeting_notes)

