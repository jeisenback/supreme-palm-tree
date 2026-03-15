"""Simple task storage for action items discovered from transcripts.

Tasks are stored in `out/tasks.json` as a list of records. This is a minimal
PoC storage used for wiring transcripts -> tasks -> scheduler reminders.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

TASKS_PATH = Path("out") / "tasks.json"


def _ensure_dir() -> None:
    TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _read_tasks() -> List[Dict]:
    _ensure_dir()
    if not TASKS_PATH.exists():
        return []
    try:
        return json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_tasks(items: List[Dict]) -> None:
    _ensure_dir()
    TASKS_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")


def add_task(title: str, description: str = "", assigned_to: Optional[str] = None, due_days: Optional[int] = None) -> Dict:
    items = _read_tasks()
    uid = str(uuid.uuid4())
    due = None
    if due_days is not None:
        due = (datetime.utcnow() + timedelta(days=due_days)).isoformat() + "Z"
    obj = {
        "id": uid,
        "title": title,
        "description": description,
        "assigned_to": assigned_to,
        "due": due,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "open",
    }
    items.append(obj)
    _write_tasks(items)
    return obj


def list_tasks() -> List[Dict]:
    return _read_tasks()


def mark_done(task_id: str) -> bool:
    items = _read_tasks()
    found = False
    for it in items:
        if it.get("id") == task_id:
            it["status"] = "done"
            found = True
    if found:
        _write_tasks(items)
    return found
