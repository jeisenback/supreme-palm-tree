"""Tests for etn/ECBA_CaseStudy/sessions/*.yaml — YAML loading and shape."""

from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
_SESSIONS_DIR = _PROJECT_ROOT / "etn" / "ECBA_CaseStudy" / "sessions"

_REQUIRED_KEYS = {"title", "agenda", "prompts"}


# ---------------------------------------------------------------------------
# Directory and file existence
# ---------------------------------------------------------------------------

def test_sessions_dir_exists():
    assert _SESSIONS_DIR.exists(), f"sessions/ directory missing: {_SESSIONS_DIR}"


def test_five_session_yaml_files():
    yamls = list(_SESSIONS_DIR.glob("session_*.yaml"))
    assert len(yamls) == 5, f"Expected 5 session YAML files, found {len(yamls)}"


@pytest.mark.parametrize("n", range(1, 6))
def test_session_yaml_exists(n):
    f = _SESSIONS_DIR / f"session_{n}.yaml"
    assert f.exists(), f"Missing: {f}"


# ---------------------------------------------------------------------------
# YAML parsing
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    """Load a YAML file using PyYAML."""
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@pytest.mark.parametrize("n", range(1, 6))
def test_session_yaml_is_valid(n):
    """Each YAML file must parse without error."""
    _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")  # raises on bad YAML


@pytest.mark.parametrize("n", range(1, 6))
def test_session_yaml_has_required_keys(n):
    data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
    missing = _REQUIRED_KEYS - set(data.keys())
    assert not missing, f"session_{n}.yaml missing keys: {missing}"


# ---------------------------------------------------------------------------
# Title field
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", range(1, 6))
def test_session_title_is_string(n):
    data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
    assert isinstance(data.get("title"), str), f"session_{n}.yaml title is not a string"


@pytest.mark.parametrize("n", range(1, 6))
def test_session_title_non_empty(n):
    data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
    assert data.get("title", "").strip(), f"session_{n}.yaml has empty title"


def test_session_titles_are_unique():
    titles = []
    for n in range(1, 6):
        data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
        titles.append(data.get("title", ""))
    assert len(titles) == len(set(titles)), f"Duplicate session titles found: {titles}"


# ---------------------------------------------------------------------------
# Agenda field
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", range(1, 6))
def test_agenda_is_list(n):
    data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
    assert isinstance(data.get("agenda"), list), f"session_{n}.yaml agenda is not a list"


@pytest.mark.parametrize("n", range(1, 6))
def test_agenda_non_empty(n):
    data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
    assert len(data.get("agenda", [])) >= 1, f"session_{n}.yaml agenda is empty"


@pytest.mark.parametrize("n", range(1, 6))
def test_agenda_items_are_strings(n):
    data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
    for item in data.get("agenda", []):
        assert isinstance(item, str), (
            f"session_{n}.yaml agenda item is not a string: {item!r}"
        )


# ---------------------------------------------------------------------------
# Prompts field
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", range(1, 6))
def test_prompts_is_list(n):
    data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
    assert isinstance(data.get("prompts"), list), f"session_{n}.yaml prompts is not a list"


@pytest.mark.parametrize("n", range(1, 6))
def test_prompts_non_empty(n):
    data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
    assert len(data.get("prompts", [])) >= 1, f"session_{n}.yaml prompts is empty"


# ---------------------------------------------------------------------------
# Practice questions (optional but validated when present)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", range(1, 6))
def test_practice_questions_structure_when_present(n):
    data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
    pqs = data.get("practice_questions")
    if pqs is None:
        pytest.skip(f"session_{n}.yaml has no practice_questions")

    assert isinstance(pqs, list), f"session_{n}.yaml practice_questions is not a list"
    for i, q in enumerate(pqs):
        assert isinstance(q, dict), f"session_{n}.yaml PQ[{i}] is not a dict"
        assert "q" in q, f"session_{n}.yaml PQ[{i}] missing 'q' key"
        assert "choices" in q, f"session_{n}.yaml PQ[{i}] missing 'choices' key"
        assert isinstance(q["choices"], list), f"session_{n}.yaml PQ[{i}] choices is not a list"
        assert len(q["choices"]) >= 2, f"session_{n}.yaml PQ[{i}] has < 2 choices"


@pytest.mark.parametrize("n", range(1, 6))
def test_practice_questions_answer_in_range(n):
    data = _load_yaml(_SESSIONS_DIR / f"session_{n}.yaml")
    pqs = data.get("practice_questions")
    if pqs is None:
        pytest.skip(f"session_{n}.yaml has no practice_questions")

    for i, q in enumerate(pqs):
        choices = q.get("choices", [])
        a = q.get("a")
        if a is not None:
            assert 0 <= int(a) < len(choices), (
                f"session_{n}.yaml PQ[{i}] answer index {a} out of range for {len(choices)} choices"
            )
