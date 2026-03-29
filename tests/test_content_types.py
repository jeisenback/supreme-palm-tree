"""Tests for apps/content_types.py — registry, session IDs, style rules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))
from content_types import CONTENT_TYPES, SESSION_IDS, SUBTYPE_IDS, STYLE_RULES, StyleRule


# ---------------------------------------------------------------------------
# CONTENT_TYPES registry
# ---------------------------------------------------------------------------

def test_all_expected_content_types_present():
    assert set(CONTENT_TYPES.keys()) == {"ecba_session", "career_accelerator", "panel_event"}


def test_required_slots_are_subset_of_slots():
    for ct, spec in CONTENT_TYPES.items():
        required = set(spec.get("required", []))
        slots = set(spec.get("slots", []))
        assert required <= slots, f"{ct}: required {required} not subset of slots {slots}"


def test_ecba_session_slots():
    slots = CONTENT_TYPES["ecba_session"]["slots"]
    assert "slides" in slots
    assert "handout" in slots
    assert "facilitator_script" in slots
    assert "practice_questions" in slots


def test_career_accelerator_has_8_subtypes():
    subtypes = CONTENT_TYPES["career_accelerator"]["subtypes"]
    assert len(subtypes) == 8


def test_career_accelerator_required():
    required = CONTENT_TYPES["career_accelerator"]["required"]
    assert "facilitator_guide" in required
    assert "participant_handout" in required


def test_panel_event_required():
    required = CONTENT_TYPES["panel_event"]["required"]
    assert "moderator_script" in required
    assert "panel_agenda" in required


# ---------------------------------------------------------------------------
# SESSION_IDS
# ---------------------------------------------------------------------------

def test_ecba_sessions_1_to_5():
    for i in range(1, 6):
        assert SESSION_IDS[i] == "ecba_session"


def test_career_accelerator_ids_100_to_107():
    ca_ids = {k: v for k, v in SESSION_IDS.items() if k >= 100}
    assert len(ca_ids) == 8
    # all values are subtype names, not "career_accelerator"
    assert all(v != "career_accelerator" for v in ca_ids.values())


def test_no_ecba_ids_outside_1_to_5():
    for k, v in SESSION_IDS.items():
        if v == "ecba_session":
            assert 1 <= k <= 5


# ---------------------------------------------------------------------------
# SUBTYPE_IDS reverse lookup
# ---------------------------------------------------------------------------

def test_subtype_ids_is_reverse_of_session_ids():
    for k, v in SESSION_IDS.items():
        if k >= 100:
            assert SUBTYPE_IDS[v] == k


def test_subtype_ids_only_contains_ca_subtypes():
    subtypes = set(CONTENT_TYPES["career_accelerator"]["subtypes"])
    assert set(SUBTYPE_IDS.keys()) == subtypes


# ---------------------------------------------------------------------------
# STYLE_RULES
# ---------------------------------------------------------------------------

def test_style_rules_count():
    assert len(STYLE_RULES) == 4


def test_style_rule_names_unique():
    names = [r.name for r in STYLE_RULES]
    assert len(names) == len(set(names))


def test_style_rule_names_expected():
    names = {r.name for r in STYLE_RULES}
    assert "max_bullets_per_slide" in names
    assert "required_learning_objective" in names
    assert "facilitator_cue_format" in names
    assert "slide_count_range" in names


def test_style_rules_are_style_rule_instances():
    for r in STYLE_RULES:
        assert isinstance(r, StyleRule)


def test_style_rule_has_message():
    for r in STYLE_RULES:
        assert r.message, f"Rule {r.name} has no message"


def test_style_rule_equality_by_name():
    r1 = StyleRule("test_rule", message="msg")
    r2 = StyleRule("test_rule", message="different msg")
    assert r1 == r2


def test_style_rule_inequality_different_names():
    r1 = StyleRule("rule_a", message="msg")
    r2 = StyleRule("rule_b", message="msg")
    assert r1 != r2
