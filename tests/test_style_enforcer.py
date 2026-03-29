"""Tests for content style enforcement rules.

Tests the _check_style logic without importing content_studio (avoids streamlit dep).
The logic is defined inline here to stay independent.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))
from content_types import STYLE_RULES


# ---------------------------------------------------------------------------
# Inline style checker (mirrors content_studio._check_style)
# ---------------------------------------------------------------------------

def _check_style(body: str, slot: str) -> list[str]:
    warnings = []
    for rule in STYLE_RULES:
        if rule.name == "required_learning_objective" and slot == "slides":
            if not re.search(rule.pattern, body, re.MULTILINE):
                warnings.append(rule.message)

        elif rule.name == "slide_count_range" and slot == "slides":
            count = len(re.findall(r"^##\s+", body, re.MULTILINE))
            if rule.min_count and count < rule.min_count:
                warnings.append(rule.message.format(count=count))
            elif rule.max_count and count > rule.max_count:
                warnings.append(rule.message.format(count=count))

        elif rule.name == "max_bullets_per_slide" and slot == "slides":
            sections = re.split(r"^##\s+", body, flags=re.MULTILINE)
            for n, section in enumerate(sections[1:], 1):
                count = len(re.findall(r"^\s*[-*]\s+", section, re.MULTILINE))
                if rule.max_count and count > rule.max_count:
                    warnings.append(rule.message.format(n=n, count=count))

        elif rule.name == "facilitator_cue_format" and "facilitator" in slot:
            bad = re.findall(r"^\[(?!FACILITATOR:)[A-Z][A-Z ]*:", body, re.MULTILINE)
            if bad:
                warnings.append("Non-standard cue(s) found — use [FACILITATOR: ...] format")
    return warnings


# ---------------------------------------------------------------------------
# required_learning_objective
# ---------------------------------------------------------------------------

def test_no_lo_warning_on_non_slides_slot():
    body = "## Slide 1\nNo learning objective."
    assert _check_style(body, "handout") == []


def test_missing_lo_triggers_warning():
    body = "## Slide 1\nContent without learning objective."
    warnings = _check_style(body, "slides")
    assert any("Learning Objective" in w for w in warnings)


def test_present_lo_no_warning():
    body = "## Learning Objective\nBy end of session...\n## Slide 2\nContent."
    warnings = _check_style(body, "slides")
    assert not any("Learning Objective" in w for w in warnings)


# ---------------------------------------------------------------------------
# max_bullets_per_slide
# ---------------------------------------------------------------------------

def test_five_bullets_no_warning():
    body = "## Learning Objective\nok\n## Slide 1\n- a\n- b\n- c\n- d\n- e\n"
    warnings = _check_style(body, "slides")
    assert not any("bullet" in w.lower() for w in warnings)


def test_six_bullets_triggers_warning():
    body = "## Learning Objective\nok\n## Slide 1\n- a\n- b\n- c\n- d\n- e\n- f\n"
    warnings = _check_style(body, "slides")
    assert any("6 bullets" in w for w in warnings)


def test_bullet_warning_names_slide_number():
    # Sections after split: [n=1]=LO (0 bullets), [n=2]=Slide 1 content (6 bullets)
    # Warning message format is "Slide {n} has {count} bullets" → "Slide 2 has 6 bullets"
    body = "## Learning Objective\nok\n## Slide 1\n- a\n- b\n- c\n- d\n- e\n- f\n"
    warnings = _check_style(body, "slides")
    assert any("Slide 2" in w for w in warnings)
    # LO section (n=1) has 0 bullets — must not appear in bullet warnings
    assert not any("Slide 1" in w for w in warnings)


def test_bullet_count_not_checked_for_non_slides():
    body = "- a\n- b\n- c\n- d\n- e\n- f\n"
    assert _check_style(body, "handout") == []


# ---------------------------------------------------------------------------
# slide_count_range (min 3, max 15)
# ---------------------------------------------------------------------------

def test_too_few_slides_triggers_warning():
    # 2 ## headers = 2 slides, min is 3
    body = "## Learning Objective\nok\n## Slide 1\nContent."
    warnings = _check_style(body, "slides")
    assert any("slide" in w.lower() or "Slide" in w for w in warnings)


def test_exactly_min_slides_no_count_warning():
    slides = "\n".join(f"## Slide {i}\nContent." for i in range(1, 4))
    body = "## Learning Objective\nok\n" + slides
    warnings = _check_style(body, "slides")
    assert not any("expected 3" in w for w in warnings)


def test_too_many_slides_triggers_warning():
    slides = "\n".join(f"## Slide {i}\nContent." for i in range(1, 18))
    body = "## Learning Objective\nok\n" + slides
    warnings = _check_style(body, "slides")
    assert any("17" in w or "slide" in w.lower() for w in warnings)


# ---------------------------------------------------------------------------
# facilitator_cue_format
# ---------------------------------------------------------------------------

def test_correct_facilitator_cue_no_warning():
    body = "[FACILITATOR: Please pause here for discussion.]"
    assert _check_style(body, "facilitator_script") == []


def test_bad_cue_format_triggers_warning():
    body = "[PRESENTER: Note for presenter]"
    warnings = _check_style(body, "facilitator_script")
    assert any("format" in w.lower() or "cue" in w.lower() for w in warnings)


def test_cue_check_not_applied_to_slides():
    # Body satisfies all other slide rules so only cue format would fire (if it checked slides)
    body = (
        "## Learning Objective\nBy end...\n"
        "## Slide 1\n[PRESENTER: Note]\n"
        "## Slide 2\nContent.\n"
        "## Slide 3\nContent.\n"
    )
    assert _check_style(body, "slides") == []


# ---------------------------------------------------------------------------
# No false positives on clean content
# ---------------------------------------------------------------------------

def test_clean_slides_deck_no_warnings():
    body = (
        "## Learning Objective\nBy the end, participants can...\n"
        "## Slide 1\n- Point 1\n- Point 2\n- Point 3\n"
        "## Slide 2\n- A\n- B\n"
        "## Slide 3\nConclusion."
    )
    warnings = _check_style(body, "slides")
    assert warnings == []


def test_clean_facilitator_script_no_warnings():
    body = "[FACILITATOR: Welcome participants.]\nSpeak clearly.\n[FACILITATOR: Pause for Q&A.]"
    assert _check_style(body, "facilitator_script") == []
