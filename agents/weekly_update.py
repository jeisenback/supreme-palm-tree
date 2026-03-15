"""Generate weekly board update from notes directory.

This module gathers markdown/plain text notes from the `notes/` directory,
concatenates them, and produces a simple weekly update. If an LLM adapter is
available it will be used to create a concise executive summary; otherwise the
update is a straightforward concatenation with headings.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
import json
import uuid
from datetime import datetime

try:
    # optional: adapter provides summarize(text) -> str
    from agents.llm_adapter import LLMAdapter, NoOpAdapter
except Exception:
    LLMAdapter = None
    NoOpAdapter = None


def gather_notes(notes_dir: str = "notes") -> List[Path]:
    p = Path(notes_dir)
    if not p.exists() or not p.is_dir():
        return []
    files = [x for x in sorted(p.iterdir()) if x.is_file() and x.suffix.lower() in (".md", ".markdown", ".txt")]
    return files


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return ""


def compose_weekly_update(title: str = "Weekly Board Update", notes_dir: str = "notes", use_llm: bool = True) -> str:
    files = gather_notes(notes_dir)
    if not files:
        return f"# {title}\n\n_No notes found in {notes_dir}_\n"

    contents = []
    for f in files:
        body = _read_file(f)
        contents.append(f"## {f.name}\n\n{body}\n")

    full_text = "\n".join(contents)

    # Try to use LLM to summarize if requested and available
    if use_llm and LLMAdapter is not None:
        try:
            adapter = LLMAdapter()
            summary = adapter.summarize(full_text)
            md = f"# {title}\n\n## Executive Summary\n\n{summary}\n\n---\n\n{full_text}"
            return md
        except Exception:
            pass

    # Fallback: simple stitched update
    md = f"# {title}\n\n## Collected Notes\n\n{full_text}"
    return md


def write_weekly_update(out_path: str, title: str = "Weekly Board Update", notes_dir: str = "notes", use_llm: bool = True) -> Path:
    """Write a weekly update directly to `out_path` (non-draft).

    This function preserves the original helper used by the CLI pre-review flow.
    """
    md = compose_weekly_update(title=title, notes_dir=notes_dir, use_llm=use_llm)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(md, encoding="utf-8")
    return p


PENDING_DIR = Path("out") / "pending"
PENDING_META = PENDING_DIR / "pending.json"
PUBLISHED_DIR = Path("out") / "published"


def _ensure_pending() -> None:
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    if not PENDING_META.exists():
        PENDING_META.write_text("[]", encoding="utf-8")


def _read_pending() -> List[dict]:
    _ensure_pending()
    try:
        return json.loads(PENDING_META.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_pending(items: List[dict]) -> None:
    _ensure_pending()
    PENDING_META.write_text(json.dumps(items, indent=2), encoding="utf-8")


def create_draft(title: str = "Weekly Board Update", notes_dir: str = "notes", use_llm: bool = True) -> dict:
    md = compose_weekly_update(title=title, notes_dir=notes_dir, use_llm=use_llm)
    _ensure_pending()
    uid = str(uuid.uuid4())
    fname = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{uid}.md"
    p = PENDING_DIR / fname
    p.write_text(md, encoding="utf-8")
    meta = {
        "id": uid,
        "title": title,
        "path": str(p.as_posix()),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    items = _read_pending()
    items.append(meta)
    _write_pending(items)
    return meta


def list_pending() -> List[dict]:
    return _read_pending()


def publish_update(update_id: str, drive_folder: Optional[str] = None, credentials_json: Optional[str] = None, credential_type: str = "service_account", oauth_token_path: Optional[str] = None) -> Optional[Path]:
    items = _read_pending()
    match = None
    for it in items:
        if it.get("id") == update_id:
            match = it
            break
    if not match:
        return None
    src = Path(match["path"])
    if not src.exists():
        # remove stale entry
        items = [i for i in items if i.get("id") != update_id]
        _write_pending(items)
        return None
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PUBLISHED_DIR / src.name
    src.replace(dest)
    # remove from pending
    items = [i for i in items if i.get("id") != update_id]
    _write_pending(items)

    # Optionally upload to Google Drive if folder or credentials provided
    if drive_folder or credentials_json or oauth_token_path:
        try:
            from integrations.gdrive.drive_client import DriveClient

            client = DriveClient(credentials_json=credentials_json, folder_id=drive_folder, credential_type=credential_type, oauth_token_path=oauth_token_path)
            try:
                client.upload_file(str(dest), mime_type="text/markdown")
            except Exception:
                # best-effort upload; do not fail publish if upload fails
                pass
        except Exception:
            # integrations may be unavailable in test env; ignore
            pass

    return dest

