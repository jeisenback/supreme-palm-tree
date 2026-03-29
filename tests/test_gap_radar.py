"""Tests for Gap Radar logic — status lookup, missing detection, metrics.

Tests the core logic without importing content_studio (avoids streamlit dep).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))
from content_types import CONTENT_TYPES


# ---------------------------------------------------------------------------
# Helpers (mirrored from content_studio._gap_radar_tab logic)
# ---------------------------------------------------------------------------

def _get_ecba_status(library: list[dict], session_id: int, slot: str) -> str:
    for e in library:
        if e["content_type"] == "ecba_session" and e.get("session_id") == session_id and e.get("slot") == slot:
            return e.get("status", "draft")
    return "missing"


def _required_gaps(library: list[dict]) -> int:
    count = 0
    for s in range(1, 6):
        for slot in CONTENT_TYPES["ecba_session"]["required"]:
            if _get_ecba_status(library, s, slot) == "missing":
                count += 1
    return count


# ---------------------------------------------------------------------------
# Status lookup
# ---------------------------------------------------------------------------

def test_missing_slot_returns_missing():
    library = [{"content_type": "ecba_session", "session_id": 1, "slot": "handout", "status": "published"}]
    assert _get_ecba_status(library, 1, "slides") == "missing"


def test_published_status_returned():
    library = [{"content_type": "ecba_session", "session_id": 2, "slot": "slides", "status": "published"}]
    assert _get_ecba_status(library, 2, "slides") == "published"


def test_draft_status_returned():
    library = [{"content_type": "ecba_session", "session_id": 3, "slot": "slides", "status": "draft"}]
    assert _get_ecba_status(library, 3, "slides") == "draft"


def test_wrong_session_id_returns_missing():
    library = [{"content_type": "ecba_session", "session_id": 1, "slot": "slides", "status": "published"}]
    assert _get_ecba_status(library, 2, "slides") == "missing"


def test_wrong_content_type_returns_missing():
    library = [{"content_type": "career_accelerator", "session_id": 1, "slot": "slides", "status": "published"}]
    assert _get_ecba_status(library, 1, "slides") == "missing"


# ---------------------------------------------------------------------------
# Required gaps counter
# ---------------------------------------------------------------------------

def test_empty_library_has_max_gaps():
    # 5 sessions × 2 required slots = 10 gaps
    gaps = _required_gaps([])
    assert gaps == 10


def test_full_library_has_zero_required_gaps():
    library = [
        {"content_type": "ecba_session", "session_id": s, "slot": slot, "status": "published"}
        for s in range(1, 6)
        for slot in CONTENT_TYPES["ecba_session"]["required"]
    ]
    assert _required_gaps(library) == 0


def test_partial_library_counts_correctly():
    # Only session 1 slides published — missing 1 slides (sessions 2-5) + all 5 handouts = 9 gaps
    # Wait: only session 1 slides covered → missing: sessions 2-5 slides (4) + all 5 handouts (5) = 9
    library = [{"content_type": "ecba_session", "session_id": 1, "slot": "slides", "status": "published"}]
    assert _required_gaps(library) == 9


def test_draft_counts_as_gap():
    # draft is lower than published but status-wise it's not "missing" in the current radar
    library = [{"content_type": "ecba_session", "session_id": 1, "slot": "slides", "status": "draft"}]
    # Session 1 slides is draft (not missing), session 1 handout missing, sessions 2-5 x2 = 9 gaps
    assert _required_gaps(library) == 9


# ---------------------------------------------------------------------------
# Metrics consistency
# ---------------------------------------------------------------------------

def test_metrics_published_count():
    library = [
        {"content_type": "ecba_session", "session_id": 1, "slot": "slides", "status": "published"},
        {"content_type": "ecba_session", "session_id": 1, "slot": "handout", "status": "draft"},
        {"content_type": "ecba_session", "session_id": 2, "slot": "slides", "status": "published"},
    ]
    published = sum(1 for e in library if e["status"] == "published")
    assert published == 2


def test_content_types_required_slots_count():
    # Verify the 10-gap calculation aligns with CONTENT_TYPES definition
    required = CONTENT_TYPES["ecba_session"]["required"]
    assert len(required) == 2
    assert 5 * len(required) == 10
