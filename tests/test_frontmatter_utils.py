"""Tests for apps/frontmatter_utils.py — read, write, scan."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))
from frontmatter_utils import read_frontmatter, write_frontmatter, scan_content_library


# ---------------------------------------------------------------------------
# read_frontmatter
# ---------------------------------------------------------------------------

def test_read_missing_file_returns_empty(tmp_path):
    meta, body = read_frontmatter(tmp_path / "nonexistent.md")
    assert meta == {}
    assert body == ""


def test_read_file_with_valid_frontmatter(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("---\nstatus: published\nsession_id: 1\n---\nBody text.", encoding="utf-8")
    meta, body = read_frontmatter(f)
    assert meta["status"] == "published"
    assert meta["session_id"] == 1
    assert "Body text." in body


def test_read_file_no_frontmatter_returns_empty_meta(tmp_path):
    f = tmp_path / "plain.md"
    f.write_text("# Just a heading\nNo frontmatter here.", encoding="utf-8")
    meta, body = read_frontmatter(f)
    assert meta == {}


def test_read_file_malformed_yaml_preserves_body(tmp_path):
    f = tmp_path / "bad.md"
    f.write_text("---\nkey: [unclosed\n---\nbody", encoding="utf-8")
    meta, body = read_frontmatter(f)
    assert meta == {}
    assert body  # raw content preserved


# ---------------------------------------------------------------------------
# write_frontmatter
# ---------------------------------------------------------------------------

def test_write_reads_back_correctly(tmp_path):
    # write_frontmatter guards path to _ETN_ROOT — patch it via a real etn subdir
    etn = tmp_path / "etn"
    etn.mkdir()
    target = etn / "file.md"

    import frontmatter_utils
    original_etn = frontmatter_utils._ETN_ROOT
    frontmatter_utils._ETN_ROOT = etn
    try:
        write_frontmatter(target, {"status": "draft", "slot": "slides"}, "# Hello\nContent.")
        meta, body = read_frontmatter(target)
        assert meta["status"] == "draft"
        assert meta["slot"] == "slides"
        assert "# Hello" in body
    finally:
        frontmatter_utils._ETN_ROOT = original_etn


def test_write_atomic_no_partial_file(tmp_path):
    etn = tmp_path / "etn"
    etn.mkdir()
    target = etn / "atomic.md"

    import frontmatter_utils
    original_etn = frontmatter_utils._ETN_ROOT
    frontmatter_utils._ETN_ROOT = etn
    try:
        write_frontmatter(target, {"status": "published"}, "content")
        assert target.exists()
        # No .tmp files should remain
        assert not list(etn.glob("*.tmp"))
    finally:
        frontmatter_utils._ETN_ROOT = original_etn


def test_write_raises_for_path_outside_etn(tmp_path):
    import frontmatter_utils
    etn = tmp_path / "etn"
    etn.mkdir()
    original_etn = frontmatter_utils._ETN_ROOT
    frontmatter_utils._ETN_ROOT = etn
    try:
        with pytest.raises(ValueError, match="outside"):
            write_frontmatter(tmp_path / "escape.md", {}, "body")
    finally:
        frontmatter_utils._ETN_ROOT = original_etn


def test_write_creates_parent_dirs(tmp_path):
    etn = tmp_path / "etn"
    etn.mkdir()
    deep = etn / "a" / "b" / "c" / "file.md"

    import frontmatter_utils
    original_etn = frontmatter_utils._ETN_ROOT
    frontmatter_utils._ETN_ROOT = etn
    try:
        write_frontmatter(deep, {"status": "draft"}, "body")
        assert deep.exists()
    finally:
        frontmatter_utils._ETN_ROOT = original_etn


# ---------------------------------------------------------------------------
# scan_content_library
# ---------------------------------------------------------------------------

def test_scan_finds_files_with_frontmatter(tmp_path):
    (tmp_path / "a.md").write_text("---\nstatus: published\n---\nbody", encoding="utf-8")
    (tmp_path / "b.md").write_text("# No frontmatter", encoding="utf-8")
    results = scan_content_library(tmp_path)
    assert len(results) == 1
    assert results[0]["status"] == "published"


def test_scan_skips_files_without_frontmatter(tmp_path):
    (tmp_path / "plain.md").write_text("just text", encoding="utf-8")
    results = scan_content_library(tmp_path)
    assert results == []


def test_scan_nonexistent_dir_returns_empty():
    results = scan_content_library(Path("/nonexistent/path/xyz"))
    assert results == []


def test_scan_returns_required_keys(tmp_path):
    (tmp_path / "c.md").write_text(
        "---\ncontent_type: ecba_session\nsession_id: 1\nslot: slides\nstatus: published\n---\nbody",
        encoding="utf-8",
    )
    results = scan_content_library(tmp_path)
    assert len(results) == 1
    r = results[0]
    assert r["content_type"] == "ecba_session"
    assert r["session_id"] == 1
    assert r["slot"] == "slides"
    assert r["status"] == "published"
    assert "path" in r


def test_scan_defaults_missing_fields(tmp_path):
    (tmp_path / "minimal.md").write_text("---\ncontent_type: ecba_session\n---\nbody",
                                          encoding="utf-8")
    results = scan_content_library(tmp_path)
    assert len(results) == 1
    r = results[0]
    assert r["status"] == "draft"   # default
    assert r["slot"] == ""          # default
    assert r["session_id"] is None  # default
