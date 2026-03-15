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
    md = compose_weekly_update(title=title, notes_dir=notes_dir, use_llm=use_llm)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(md, encoding="utf-8")
    return p
