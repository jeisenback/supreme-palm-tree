"""Tests for etn/templates/ — existence, frontmatter completeness, status."""

import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "apps"))
from frontmatter_utils import read_frontmatter
from content_types import CONTENT_TYPES

_TEMPLATES_DIR = _PROJECT_ROOT / "etn" / "templates"
_CA_DIR = _TEMPLATES_DIR / "career_accelerator"
_PE_DIR = _TEMPLATES_DIR / "panel_event"

# ---------------------------------------------------------------------------
# Career Accelerator templates
# ---------------------------------------------------------------------------

_CA_SUBTYPES = CONTENT_TYPES["career_accelerator"]["subtypes"]

@pytest.mark.parametrize("subtype", _CA_SUBTYPES)
def test_ca_template_exists(subtype):
    f = _CA_DIR / f"{subtype}.md"
    assert f.exists(), f"Missing CA template: {f}"


def test_ca_pre_work_template_exists():
    assert (_CA_DIR / "pre_work.md").exists()


def test_ca_template_count():
    templates = list(_CA_DIR.glob("*.md"))
    # 8 subtypes + pre_work = 9
    assert len(templates) >= 9, f"Expected ≥9 CA templates, found {len(templates)}"


# ---------------------------------------------------------------------------
# Panel event templates
# ---------------------------------------------------------------------------

_PE_REQUIRED = ["moderator_script", "panel_agenda", "panelist_bios"]

@pytest.mark.parametrize("slot", _PE_REQUIRED)
def test_panel_template_exists(slot):
    f = _PE_DIR / f"{slot}.md"
    assert f.exists(), f"Missing panel template: {f}"


def test_panel_template_count():
    templates = list(_PE_DIR.glob("*.md"))
    assert len(templates) >= 3, f"Expected ≥3 panel templates, found {len(templates)}"


# ---------------------------------------------------------------------------
# Frontmatter completeness
# ---------------------------------------------------------------------------

def _all_templates():
    return list(_CA_DIR.glob("*.md")) + list(_PE_DIR.glob("*.md"))


@pytest.mark.parametrize("path", _all_templates(), ids=lambda p: p.name)
def test_template_has_content_type(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("content_type"), f"{path.name} missing content_type"


@pytest.mark.parametrize("path", _all_templates(), ids=lambda p: p.name)
def test_template_has_slot(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("slot"), f"{path.name} missing slot"


@pytest.mark.parametrize("path", _all_templates(), ids=lambda p: p.name)
def test_template_has_status(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("status"), f"{path.name} missing status"


@pytest.mark.parametrize("path", _all_templates(), ids=lambda p: p.name)
def test_template_status_is_template(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("status") == "template", (
        f"{path.name}: expected status=template, got {meta.get('status')!r}"
    )


# ---------------------------------------------------------------------------
# Content type consistency
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", list(_CA_DIR.glob("*.md")), ids=lambda p: p.name)
def test_ca_template_content_type(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("content_type") == "career_accelerator", (
        f"{path.name}: expected career_accelerator, got {meta.get('content_type')!r}"
    )


@pytest.mark.parametrize("path", list(_PE_DIR.glob("*.md")), ids=lambda p: p.name)
def test_panel_template_content_type(path):
    meta, _ = read_frontmatter(path)
    assert meta.get("content_type") == "panel_event", (
        f"{path.name}: expected panel_event, got {meta.get('content_type')!r}"
    )


# ---------------------------------------------------------------------------
# Body is non-empty
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", _all_templates(), ids=lambda p: p.name)
def test_template_has_non_empty_body(path):
    _, body = read_frontmatter(path)
    assert len(body.strip()) > 50, f"{path.name} body is too short (< 50 chars)"
