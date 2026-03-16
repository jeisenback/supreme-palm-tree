"""Approval registry for scraper sources.

Stores approvals in `config/sources-approved.yaml` (YAML) when PyYAML is
available; otherwise falls back to JSON at the same path. Provides simple
functions to add/revoke/list approvals.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


_PATH = Path("config") / "sources-approved.yaml"


def _ensure_config_dir() -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)


def _read() -> List[Dict[str, Any]]:
    _ensure_config_dir()
    if not _PATH.exists():
        return []
    text = _PATH.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or []
        if isinstance(data, list):
            return data
        return []
    except Exception:
        # fallback to JSON
        try:
            return json.loads(text)
        except Exception:
            return []


def _write(data: List[Dict[str, Any]]) -> None:
    _ensure_config_dir()
    try:
        import yaml  # type: ignore

        _PATH.write_text(yaml.safe_dump(data), encoding="utf-8")
        return
    except Exception:
        _PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

def get_approval(source_id: str) -> Optional[Dict[str, Any]]:
    """Return the approval metadata object for `source_id`, or None if not approved.

    This helper is convenient for runtime enforcement checks.
    """
    data = _read()
    for d in data:
        if d.get("id") == source_id:
            return d
    return None

def list_approved() -> List[Dict[str, Any]]:
    return _read()


def approve_source(source_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    data = _read()
    if any(d.get("id") == source_id for d in data):
        return
    obj = {"id": source_id}
    if metadata:
        obj.update(metadata)
    data.append(obj)
    _write(data)


def update_approval(source_id: str, metadata: Dict[str, Any]) -> None:
    """Update or add an approval metadata dict for `source_id`.

    Keys in `metadata` are merged into the existing approval object; None
    values are treated as deletions of the key.
    """
    data = _read()
    found = False
    for i, d in enumerate(data):
        if d.get("id") == source_id:
            found = True
            for k, v in metadata.items():
                if v is None:
                    d.pop(k, None)
                else:
                    d[k] = v
            data[i] = d
            break
    if not found:
        obj = {"id": source_id}
        obj.update({k: v for k, v in metadata.items() if v is not None})
        data.append(obj)
    _write(data)


def remove_approval_field(source_id: str, field: str) -> None:
    """Remove a single metadata field from an approval, if present."""
    data = _read()
    changed = False
    for i, d in enumerate(data):
        if d.get("id") == source_id:
            if field in d:
                d.pop(field, None)
                data[i] = d
                changed = True
            break
    if changed:
        _write(data)


def revoke_source(source_id: str) -> None:
    data = _read()
    data = [d for d in data if d.get("id") != source_id]
    _write(data)
