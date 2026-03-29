"""Tests for panel mode assets — panel template files and their frontmatter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))
from frontmatter_utils import read_frontmatter

_PROJECT_ROOT = Path(__file__).parent.parent
_PANEL_DIR = _PROJECT_ROOT / "etn" / "templates" / "panel_event"


# ---------------------------------------------------------------------------
# Directory existence
# ---------------------------------------------------------------------------

def test_panel_event_dir_exists():
    assert _PANEL_DIR.exists(), f"panel_event directory missing: {_PANEL_DIR}"


def test_panel_event_dir_has_md_files():
    templates = list(_PANEL_DIR.glob("*.md"))
    assert len(templates) >= 3, f"Expected ≥3 panel templates, found {len(templates)}"


# ---------------------------------------------------------------------------
# Required file existence
# ---------------------------------------------------------------------------

def test_moderator_script_exists():
    assert (_PANEL_DIR / "moderator_script.md").exists()


def test_panel_agenda_exists():
    assert (_PANEL_DIR / "panel_agenda.md").exists()


def test_panelist_bios_exists():
    assert (_PANEL_DIR / "panelist_bios.md").exists()


# ---------------------------------------------------------------------------
# Frontmatter: content_type = panel_event
# ---------------------------------------------------------------------------

import pytest

_PANEL_TEMPLATES = list(_PANEL_DIR.glob("*.md")) if _PANEL_DIR.exists() else []


@pytest.mark.parametrize("path", _PANEL_TEMPLATES, ids=lambda p: p.name)
def test_panel_content_type(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("content_type") == "panel_event", (
        f"{path.name}: expected content_type=panel_event, got {meta.get('content_type')!r}"
    )


@pytest.mark.parametrize("path", _PANEL_TEMPLATES, ids=lambda p: p.name)
def test_panel_status_is_template(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("status") == "template", (
        f"{path.name}: expected status=template, got {meta.get('status')!r}"
    )


@pytest.mark.parametrize("path", _PANEL_TEMPLATES, ids=lambda p: p.name)
def test_panel_has_slot(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("slot"), f"{path.name} missing slot"


@pytest.mark.parametrize("path", _PANEL_TEMPLATES, ids=lambda p: p.name)
def test_panel_slot_is_known(path):
    from content_types import CONTENT_TYPES
    meta, _ = read_frontmatter(path)
    slot = meta.get("slot", "")
    known_slots = CONTENT_TYPES["panel_event"]["slots"]
    assert slot in known_slots, (
        f"{path.name}: slot {slot!r} not in known panel_event slots {known_slots}"
    )


# ---------------------------------------------------------------------------
# Frontmatter: slots match filenames for required files
# ---------------------------------------------------------------------------

def test_moderator_script_slot_value():
    meta, _ = read_frontmatter(_PANEL_DIR / "moderator_script.md")
    assert meta.get("slot") == "moderator_script"


def test_panel_agenda_slot_value():
    meta, _ = read_frontmatter(_PANEL_DIR / "panel_agenda.md")
    assert meta.get("slot") == "panel_agenda"


def test_panelist_bios_slot_value():
    meta, _ = read_frontmatter(_PANEL_DIR / "panelist_bios.md")
    assert meta.get("slot") == "panelist_bios"


# ---------------------------------------------------------------------------
# Body content checks
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", _PANEL_TEMPLATES, ids=lambda p: p.name)
def test_panel_template_non_empty_body(path):
    _, body = read_frontmatter(path)
    assert len(body.strip()) > 50, f"{path.name}: body is too short"


def test_moderator_script_has_facilitator_cues():
    """Moderator script should include at least one [MODERATOR: ...] cue."""
    _, body = read_frontmatter(_PANEL_DIR / "moderator_script.md")
    assert "[MODERATOR:" in body, "moderator_script.md should contain [MODERATOR: ...] cues"


def test_panel_agenda_has_table_or_heading():
    """Panel agenda should have markdown structure."""
    _, body = read_frontmatter(_PANEL_DIR / "panel_agenda.md")
    has_structure = "|" in body or "##" in body or "#" in body
    assert has_structure, "panel_agenda.md should have markdown table or headings"
