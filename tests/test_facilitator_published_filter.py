"""Tests for the _is_published() helper in apps/facilitator_ui.py.

Avoids importing facilitator_ui (Streamlit dep) by duplicating the helper
inline — identical logic, tested independently.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))
from frontmatter_utils import read_frontmatter


# ---------------------------------------------------------------------------
# Inline helper — mirrors facilitator_ui._is_published exactly
# ---------------------------------------------------------------------------

def _is_published(path: Path) -> bool:
    """Return True if file is published or has no frontmatter (legacy file)."""
    meta, _ = read_frontmatter(path)
    if not meta:
        return True  # no frontmatter → legacy file, show it
    return meta.get("status") not in ("draft", "template")


# ---------------------------------------------------------------------------
# Files without frontmatter (legacy) → always published
# ---------------------------------------------------------------------------

def test_no_frontmatter_returns_true(tmp_path):
    f = tmp_path / "plain.md"
    f.write_text("# A plain markdown file\nNo frontmatter here.", encoding="utf-8")
    assert _is_published(f) is True


def test_missing_file_returns_true(tmp_path):
    # read_frontmatter returns ({}, "") for missing files — treated as legacy
    assert _is_published(tmp_path / "nonexistent.md") is True


def test_empty_file_returns_true(tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("", encoding="utf-8")
    assert _is_published(f) is True


# ---------------------------------------------------------------------------
# Status: published
# ---------------------------------------------------------------------------

def test_status_published_returns_true(tmp_path):
    f = tmp_path / "pub.md"
    f.write_text("---\nstatus: published\n---\nbody", encoding="utf-8")
    assert _is_published(f) is True


# ---------------------------------------------------------------------------
# Status: draft → not published
# ---------------------------------------------------------------------------

def test_status_draft_returns_false(tmp_path):
    f = tmp_path / "draft.md"
    f.write_text("---\nstatus: draft\n---\nbody", encoding="utf-8")
    assert _is_published(f) is False


# ---------------------------------------------------------------------------
# Status: template → not published
# ---------------------------------------------------------------------------

def test_status_template_returns_false(tmp_path):
    f = tmp_path / "template.md"
    f.write_text("---\nstatus: template\n---\nbody", encoding="utf-8")
    assert _is_published(f) is False


# ---------------------------------------------------------------------------
# Missing status key in frontmatter
# ---------------------------------------------------------------------------

def test_no_status_key_returns_true(tmp_path):
    """Frontmatter present but no status key → not draft/template → published."""
    f = tmp_path / "no_status.md"
    f.write_text("---\ncontent_type: ecba_session\n---\nbody", encoding="utf-8")
    assert _is_published(f) is True


# ---------------------------------------------------------------------------
# Consistency: published filter keeps published, removes draft/template
# ---------------------------------------------------------------------------

def test_filter_keeps_published_and_legacy(tmp_path):
    (tmp_path / "a.md").write_text("---\nstatus: published\n---\nbody", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Legacy\nNo frontmatter.", encoding="utf-8")
    (tmp_path / "c.md").write_text("---\nstatus: draft\n---\nbody", encoding="utf-8")
    (tmp_path / "d.md").write_text("---\nstatus: template\n---\nbody", encoding="utf-8")

    docs = sorted(tmp_path.glob("*.md"))
    visible = [d for d in docs if _is_published(d)]
    names = [d.name for d in visible]

    assert "a.md" in names
    assert "b.md" in names
    assert "c.md" not in names
    assert "d.md" not in names


def test_filter_empty_dir_returns_empty(tmp_path):
    docs = list(tmp_path.glob("*.md"))
    visible = [d for d in docs if _is_published(d)]
    assert visible == []
