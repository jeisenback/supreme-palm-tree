"""Tests for ECBA session file frontmatter — verifying the Sprint 5 backfill.

Scans the live etn/ECBA_CaseStudy/ directory and validates that all
managed markdown files have correct frontmatter fields.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))
from frontmatter_utils import read_frontmatter, scan_content_library
from content_types import CONTENT_TYPES

_PROJECT_ROOT = Path(__file__).parent.parent
_ECBA_DIR = _PROJECT_ROOT / "etn" / "ECBA_CaseStudy"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ecba_managed_files() -> list[Path]:
    """Return .md files in ECBA_CaseStudy that have frontmatter."""
    result = []
    for md in sorted(_ECBA_DIR.rglob("*.md")):
        meta, _ = read_frontmatter(md)
        if meta:
            result.append(md)
    return result


_MANAGED = _ecba_managed_files()


# ---------------------------------------------------------------------------
# Minimum coverage: at least 10 managed files after backfill
# ---------------------------------------------------------------------------

def test_ecba_dir_exists():
    assert _ECBA_DIR.exists(), f"ECBA directory missing: {_ECBA_DIR}"


def test_managed_files_minimum_count():
    assert len(_MANAGED) >= 10, (
        f"Expected ≥10 managed ECBA files after backfill, found {len(_MANAGED)}"
    )


# ---------------------------------------------------------------------------
# Every managed file must have required frontmatter keys
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", _MANAGED, ids=lambda p: p.relative_to(_ECBA_DIR).as_posix())
def test_has_content_type(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("content_type"), f"{path.name} missing content_type"


@pytest.mark.parametrize("path", _MANAGED, ids=lambda p: p.relative_to(_ECBA_DIR).as_posix())
def test_has_slot(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("slot"), f"{path.name} missing slot"


@pytest.mark.parametrize("path", _MANAGED, ids=lambda p: p.relative_to(_ECBA_DIR).as_posix())
def test_has_status(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("status"), f"{path.name} missing status"


@pytest.mark.parametrize("path", _MANAGED, ids=lambda p: p.relative_to(_ECBA_DIR).as_posix())
def test_has_session_id(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("session_id") is not None, f"{path.name} missing session_id"


# ---------------------------------------------------------------------------
# Content type correctness for ECBA files
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", _MANAGED, ids=lambda p: p.relative_to(_ECBA_DIR).as_posix())
def test_content_type_is_ecba_session(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("content_type") == "ecba_session", (
        f"{path.name}: expected content_type=ecba_session, got {meta.get('content_type')!r}"
    )


@pytest.mark.parametrize("path", _MANAGED, ids=lambda p: p.relative_to(_ECBA_DIR).as_posix())
def test_slot_is_known(path):
    meta, _ = read_frontmatter(path)
    slot = meta.get("slot", "")
    known = CONTENT_TYPES["ecba_session"]["slots"]
    assert slot in known, f"{path.name}: slot {slot!r} not in {known}"


@pytest.mark.parametrize("path", _MANAGED, ids=lambda p: p.relative_to(_ECBA_DIR).as_posix())
def test_session_id_in_valid_range(path):
    meta, _ = read_frontmatter(path)
    sid = meta.get("session_id")
    assert isinstance(sid, int), f"{path.name}: session_id should be int, got {type(sid)}"
    assert 0 <= sid <= 5, f"{path.name}: session_id={sid} out of range [0-5]"


@pytest.mark.parametrize("path", _MANAGED, ids=lambda p: p.relative_to(_ECBA_DIR).as_posix())
def test_status_is_valid(path):
    meta, _ = read_frontmatter(path)
    status = meta.get("status", "")
    valid = {"draft", "published", "review", "archived"}
    assert status in valid, (
        f"{path.name}: status {status!r} not in {valid}"
    )


# ---------------------------------------------------------------------------
# Published count: core session files (non-review-package, non-B-variant)
# ---------------------------------------------------------------------------

def test_published_slides_exist():
    """At least one published slides file should exist (session 1 coverage)."""
    library = scan_content_library(_ECBA_DIR)
    published_slides = [
        e for e in library
        if e["content_type"] == "ecba_session"
        and e["slot"] == "slides"
        and e["status"] == "published"
    ]
    assert len(published_slides) >= 1, (
        f"Expected ≥1 published slides file, found {len(published_slides)}"
    )


def test_published_handouts_exist():
    """At least some handout files should be published."""
    library = scan_content_library(_ECBA_DIR)
    published_handouts = [
        e for e in library
        if e["content_type"] == "ecba_session"
        and e["slot"] == "handout"
        and e["status"] == "published"
    ]
    assert len(published_handouts) >= 1, "No published handout files found"


def test_scan_finds_ecba_library():
    """scan_content_library should find all managed ECBA files."""
    library = scan_content_library(_ECBA_DIR)
    assert len(library) >= 10, (
        f"scan_content_library found only {len(library)} files in ECBA dir"
    )


def test_no_ecba_files_are_templates():
    """ECBA session files should not have status=template (that's for etn/templates/)."""
    library = scan_content_library(_ECBA_DIR)
    template_status = [e for e in library if e["status"] == "template"]
    assert template_status == [], (
        f"ECBA session files should not have status=template; found: "
        f"{[str(e['path']) for e in template_status]}"
    )


# ---------------------------------------------------------------------------
# Body non-empty
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", _MANAGED, ids=lambda p: p.relative_to(_ECBA_DIR).as_posix())
def test_body_non_empty(path):
    _, body = read_frontmatter(path)
    assert len(body.strip()) > 20, f"{path.name}: body is too short"
