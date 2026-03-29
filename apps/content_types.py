"""
Content type registry and style rules for IIBA ETN curriculum platform.
No Streamlit imports — safe to use in tests and non-UI contexts.
Style rules are loaded dynamically from ECBA_Style_Guide.md at startup (P2);
falls back to hardcoded defaults if the file or section is missing.
"""

from pathlib import Path

_STYLE_GUIDE_PATH = Path(__file__).parent.parent / "etn" / "ECBA_CaseStudy" / "Facilitator" / "ECBA_Style_Guide.md"

# ---------------------------------------------------------------------------
# Content type registry
# ---------------------------------------------------------------------------

CONTENT_TYPES = {
    "ecba_session": {
        "slots": ["slides", "handout", "facilitator_script", "practice_questions"],
        "required": ["slides", "handout"],
    },
    "career_accelerator": {
        "subtypes": [
            "career_mapping",
            "resume_lab",
            "mock_interview",
            "case_workshop",
            "requirements_fundamentals",
            "skills_not_titles_panel",
            "career_retrospective",
            "hiring_manager_perspective",
        ],
        "slots": ["facilitator_guide", "participant_handout", "pre_work", "rubric"],
        "required": ["facilitator_guide", "participant_handout"],
    },
    "panel_event": {
        "slots": [
            "moderator_script",
            "panel_agenda",
            "panelist_bios",
            "networking_rotation",
            "post_event_followup",
        ],
        "required": ["moderator_script", "panel_agenda"],
    },
}

# Session ID scheme:
#   ECBA sessions:           1–5  (keyed by session number)
#   Career Accelerator:    100–107 (keyed by subtype name)
#   Multiple instances of the same type use string suffixes: "101_v2", "101_v3"

SESSION_IDS = {
    # ECBA
    1: "ecba_session",
    2: "ecba_session",
    3: "ecba_session",
    4: "ecba_session",
    5: "ecba_session",
    # Career Accelerator — int → subtype name
    100: "career_mapping",
    101: "resume_lab",
    102: "mock_interview",
    103: "case_workshop",
    104: "requirements_fundamentals",
    105: "skills_not_titles_panel",
    106: "career_retrospective",
    107: "hiring_manager_perspective",
}

# Reverse lookup: subtype name → canonical session_id int
SUBTYPE_IDS = {v: k for k, v in SESSION_IDS.items() if k >= 100}


# ---------------------------------------------------------------------------
# Style rules
# ---------------------------------------------------------------------------

class StyleRule:
    """Value object describing one content style rule.

    Attributes:
        name:       Unique machine-readable rule identifier.
        max_count:  Upper bound (bullets per slide, or total slide count).
        min_count:  Lower bound (slide count).
        pattern:    Regex pattern that must be present (required_*) or absent (format rules).
        message:    Human-readable warning template. Supports {n}, {count} placeholders.
    """

    __slots__ = ("name", "max_count", "min_count", "pattern", "message")

    def __init__(self, name, *, max_count=None, min_count=None, pattern=None, message):
        self.name = name
        self.max_count = max_count
        self.min_count = min_count
        self.pattern = pattern
        self.message = message

    def __repr__(self):
        return f"StyleRule({self.name!r})"

    def __eq__(self, other):
        return isinstance(other, StyleRule) and self.name == other.name


# Hardcoded defaults — used when ECBA_Style_Guide.md is absent or its
# ## MACHINE-READABLE STYLE RULES section is removed/malformed.
_HARDCODED_STYLE_RULES = [
    StyleRule(
        "max_bullets_per_slide",
        max_count=5,
        message="Slide {n} has {count} bullets (max 5)",
    ),
    StyleRule(
        "required_learning_objective",
        pattern=r"^## Learning Objective",
        message="Missing '## Learning Objective' header",
    ),
    StyleRule(
        "facilitator_cue_format",
        pattern=r"\[FACILITATOR:",
        message="Facilitator cue on line {n} should use [FACILITATOR: ...] format",
    ),
    StyleRule(
        "slide_count_range",
        min_count=3,
        max_count=15,
        message="Session has {count} slides (expected 3–15)",
    ),
]


def _load_style_rules() -> list:
    """Return StyleRule list from ECBA_Style_Guide.md, or hardcoded fallback."""
    try:
        from frontmatter_utils import parse_style_rules as _parse
        raw = _parse(_STYLE_GUIDE_PATH)
        if raw:
            return [
                StyleRule(
                    r["name"],
                    max_count=r.get("max_count"),
                    min_count=r.get("min_count"),
                    pattern=r.get("pattern"),
                    message=r["message"],
                )
                for r in raw
            ]
    except Exception:
        pass
    return list(_HARDCODED_STYLE_RULES)


STYLE_RULES = _load_style_rules()

