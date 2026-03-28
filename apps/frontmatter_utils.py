"""
Frontmatter read/write/scan utilities for the IIBA ETN content library.
No Streamlit import — safe to use in tests and non-UI contexts.

All writes are atomic (tempfile + os.replace) and path-guarded to etn/.
"""

import os
import tempfile
from pathlib import Path

import frontmatter as _fm  # python-frontmatter

# ---------------------------------------------------------------------------
# Path guard
# ---------------------------------------------------------------------------

# Resolved once at import time so it's independent of the caller's CWD.
# apps/frontmatter_utils.py lives one level below the project root.
_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
_ETN_ROOT = _PROJECT_ROOT / "etn"


def _assert_within_etn(path: Path) -> None:
    """Raise ValueError if resolved path escapes etn/.

    Guards against traversal inputs like '../../etc/passwd' or
    absolute paths outside the project.
    """
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(_ETN_ROOT)
    except ValueError:
        raise ValueError(
            f"Path {str(path)!r} resolves to {resolved!r}, "
            f"which is outside the allowed directory {_ETN_ROOT!r}"
        )


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def read_frontmatter(path: Path) -> tuple[dict, str]:
    """Read YAML frontmatter and body from a markdown file.

    Returns:
        (metadata_dict, body_str)

    Behaviour on error:
        - File not found  → ({}, "")
        - Malformed YAML  → ({}, raw_file_contents)  — body is preserved
    """
    path = Path(path)
    if not path.exists():
        return {}, ""

    try:
        with open(path, encoding="utf-8", newline="") as fh:
            post = _fm.load(fh)
        return dict(post.metadata), post.content
    except Exception:
        # Malformed YAML — return empty metadata, preserve raw body
        try:
            body = path.read_text(encoding="utf-8")
        except Exception:
            body = ""
        return {}, body


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def write_frontmatter(path: Path, metadata: dict, body: str) -> None:
    """Atomically write frontmatter + body to path.

    Uses tempfile + os.replace so the file is never left in a partial state.

    Raises:
        ValueError   if path escapes etn/ (traversal guard).
        OSError      on filesystem failure — caller decides how to surface this.
    """
    path = Path(path)
    _assert_within_etn(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    post = _fm.Post(body, **metadata)
    content = _fm.dumps(post)

    # Write to a temp file in the same directory, then atomically rename.
    # Same-directory temp ensures os.replace stays on the same filesystem.
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

def scan_content_library(base_dir: Path) -> list[dict]:
    """Scan base_dir recursively for .md files that have YAML frontmatter.

    Files without frontmatter (plain markdown, READMEs, etc.) are skipped.

    Returns a list of dicts, one per file:
        path          Path  — absolute resolved path
        status        str   — 'draft' | 'published'  (default: 'draft')
        content_type  str   — e.g. 'ecba_session'     (default: '')
        session_id    any   — int or str like '101_v2' (default: None)
        slot          str   — e.g. 'slides'            (default: '')
        subtype       str   — e.g. 'resume_lab'        (default: '')
        last_modified str   — ISO date string          (default: '')
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return []

    results = []
    for md_file in sorted(base_dir.rglob("*.md")):
        metadata, _ = read_frontmatter(md_file)
        if not metadata:
            continue  # no frontmatter — not a managed content file
        results.append({
            "path": md_file.resolve(),
            "status": metadata.get("status", "draft"),
            "content_type": metadata.get("content_type", ""),
            "session_id": metadata.get("session_id"),
            "slot": metadata.get("slot", ""),
            "subtype": metadata.get("subtype", ""),
            "last_modified": str(metadata.get("last_modified", "")),
        })
    return results
