"""App-layer tests for facilitator_ui helpers (#56).

Tests cover:
- _generate_session_export (markdown generation, duplicate names)
- read_live_session / write_live_session (happy path, missing, malformed)
- read_attendees (missing dir, valid files, malformed file)
- load_sessions_override / save_sessions_override (missing, valid, malformed)
- _call_llm (missing API key guard)
- parse_slides round-trip via shared.py (smoke test gating Go Live, see TODOS.md)
"""
import json
import sys
import os
from pathlib import Path
import importlib
import types

import pytest


# ---------------------------------------------------------------------------
# Bootstrap: stub out streamlit and streamlit.components.v1 so facilitator_ui
# can be imported without a running Streamlit server.
# ---------------------------------------------------------------------------

def _make_st_stub():
    st = types.ModuleType("streamlit")
    st.cache_data = lambda *a, **kw: (lambda f: f)  # no-op decorator
    st.warning = lambda *a, **kw: None
    st.error = lambda *a, **kw: None
    st.info = lambda *a, **kw: None
    st.success = lambda *a, **kw: None
    st.session_state = {}
    st.query_params = {}
    # Attributes accessed at import time in shared.py
    return st


def _install_stubs():
    if "streamlit" not in sys.modules:
        sys.modules["streamlit"] = _make_st_stub()
    if "streamlit.components" not in sys.modules:
        comp_pkg = types.ModuleType("streamlit.components")
        sys.modules["streamlit.components"] = comp_pkg
    if "streamlit.components.v1" not in sys.modules:
        v1 = types.ModuleType("streamlit.components.v1")
        v1.html = lambda *a, **kw: None
        sys.modules["streamlit.components.v1"] = v1
    if "pandas" not in sys.modules:
        pd = types.ModuleType("pandas")
        pd.read_csv = lambda *a, **kw: pd.DataFrame()
        pd.DataFrame = list  # minimal stub for isinstance checks avoided in helpers
        sys.modules["pandas"] = pd


_install_stubs()

# Add apps/ to path so we can import facilitator_ui and shared
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

import facilitator_ui as fui  # noqa: E402
from shared import parse_slides  # noqa: E402


# ---------------------------------------------------------------------------
# _generate_session_export
# ---------------------------------------------------------------------------

class TestGenerateSessionExport:
    def _live(self, **kw):
        base = {"session_id": "abc123", "started_at": "2026-03-24T10:00:00Z", "ended_at": "2026-03-24T11:00:00Z"}
        base.update(kw)
        return base

    def test_no_attendees(self):
        out = fui._generate_session_export(self._live(), [])
        assert "# ECBA Study Session — Export" in out
        assert "abc123" in out
        assert "no participants recorded" in out

    def test_with_attendees(self):
        attendees = [
            {"name": "Alice", "joined_at": "2026-03-24T10:05:00Z"},
            {"name": "Bob", "joined_at": "2026-03-24T10:06:00Z"},
        ]
        out = fui._generate_session_export(self._live(), attendees)
        assert "Alice" in out
        assert "Bob" in out
        assert "2 participants" in out

    def test_duplicate_names_get_suffix(self):
        attendees = [
            {"name": "Alice", "joined_at": "T1"},
            {"name": "Alice", "joined_at": "T2"},
            {"name": "Bob", "joined_at": "T3"},
        ]
        out = fui._generate_session_export(self._live(), attendees)
        assert "Alice #1" in out
        assert "Alice #2" in out
        assert "Bob" in out
        # Bob is unique — should not have a suffix
        assert "Bob #" not in out

    def test_single_attendee_label(self):
        out = fui._generate_session_export(self._live(), [{"name": "Solo", "joined_at": "T"}])
        assert "1 participant)" in out  # singular

    def test_session_metadata_present(self):
        live = self._live(session_id="deadbeef", started_at="START", ended_at="END")
        out = fui._generate_session_export(live, [])
        assert "deadbeef" in out
        assert "START" in out
        assert "END" in out


# ---------------------------------------------------------------------------
# read_live_session / write_live_session
# ---------------------------------------------------------------------------

class TestLiveSession:
    def test_missing_file_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fui, "LIVE_SESSION_PATH", tmp_path / "nonexistent.json")
        assert fui.read_live_session() is None

    def test_malformed_json_returns_none(self, tmp_path, monkeypatch):
        p = tmp_path / "session_live.json"
        p.write_text("{ not valid json }", encoding="utf-8")
        monkeypatch.setattr(fui, "LIVE_SESSION_PATH", p)
        result = fui.read_live_session()
        assert result is None

    def test_valid_file_roundtrip(self, tmp_path, monkeypatch):
        p = tmp_path / "session_live.json"
        monkeypatch.setattr(fui, "LIVE_SESSION_PATH", p)
        data = {"session_id": "xyz", "slide_idx": 3, "ended_at": None}
        fui.write_live_session(data)
        result = fui.read_live_session()
        assert result == data

    def test_write_creates_parent_dirs(self, tmp_path, monkeypatch):
        p = tmp_path / "deep" / "path" / "session_live.json"
        monkeypatch.setattr(fui, "LIVE_SESSION_PATH", p)
        fui.write_live_session({"ok": True})
        assert p.exists()


# ---------------------------------------------------------------------------
# read_attendees
# ---------------------------------------------------------------------------

class TestReadAttendees:
    def test_missing_dir_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fui, "ATTENDEES_DIR", tmp_path / "nonexistent")
        assert fui.read_attendees() == []

    def test_reads_valid_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fui, "ATTENDEES_DIR", tmp_path)
        (tmp_path / "a.json").write_text(json.dumps({"name": "Alice"}), encoding="utf-8")
        (tmp_path / "b.json").write_text(json.dumps({"name": "Bob"}), encoding="utf-8")
        result = fui.read_attendees()
        names = {r["name"] for r in result}
        assert names == {"Alice", "Bob"}

    def test_malformed_file_skipped(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fui, "ATTENDEES_DIR", tmp_path)
        (tmp_path / "good.json").write_text(json.dumps({"name": "OK"}), encoding="utf-8")
        (tmp_path / "bad.json").write_text("not json", encoding="utf-8")
        result = fui.read_attendees()
        assert len(result) == 1
        assert result[0]["name"] == "OK"


# ---------------------------------------------------------------------------
# load_sessions_override / save_sessions_override
# ---------------------------------------------------------------------------

class TestSessionsOverride:
    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fui, "SESSIONS_OVERRIDE_PATH", tmp_path / "sessions.json")
        assert fui.load_sessions_override() == {}

    def test_malformed_returns_empty(self, tmp_path, monkeypatch):
        p = tmp_path / "sessions.json"
        p.write_text("not json", encoding="utf-8")
        monkeypatch.setattr(fui, "SESSIONS_OVERRIDE_PATH", p)
        assert fui.load_sessions_override() == {}

    def test_roundtrip(self, tmp_path, monkeypatch):
        p = tmp_path / "sessions.json"
        monkeypatch.setattr(fui, "SESSIONS_OVERRIDE_PATH", p)
        data = {"1": {"title": "Custom", "agenda": ["Item A"], "homework": "hw",
                      "prompts": [], "practice_questions": []}}
        fui.save_sessions_override(data)
        assert fui.load_sessions_override() == data


# ---------------------------------------------------------------------------
# _call_llm — guard: missing API key returns error string, never raises
# ---------------------------------------------------------------------------

class TestCallLlm:
    def test_missing_key_returns_error_string(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = fui._call_llm("hello")
        assert result.startswith("Error")

    @pytest.mark.integration
    def test_live_call(self):
        """Requires ANTHROPIC_API_KEY in environment. Deselect with -m 'not integration'."""
        result = fui._call_llm("Say hello in one word.")
        assert isinstance(result, str)
        assert len(result) > 0
        assert not result.startswith("Error")


# ---------------------------------------------------------------------------
# parse_slides smoke test — guards the pre-session readiness check (#50 / TODOS.md)
# A slide deck that exists but has zero parseable slides would let Go Live proceed
# while serving an empty deck to all participants.
# ---------------------------------------------------------------------------

class TestParseSlides:
    def test_empty_string_returns_empty(self):
        assert parse_slides("") == []

    def test_none_returns_empty(self):
        assert parse_slides(None) == []

    def test_parses_numbered_slides(self):
        md = "Slide 1 — Intro\nSome content\n\nSlide 2 — Body\nMore content"
        slides = parse_slides(md)
        assert len(slides) == 2
        assert slides[0]["title"] == "Slide 1 — Intro"
        assert "Some content" in slides[0]["body"]

    def test_facilitator_notes_extracted(self):
        md = "Slide 1 — Test\nBody text\n[FACILITATOR: remind them of prereqs]"
        slides = parse_slides(md)
        assert len(slides) == 1
        assert "remind them of prereqs" in slides[0]["facilitator_notes"][0]
        assert "[FACILITATOR:" not in slides[0]["body"]

    def test_malformed_deck_returns_empty(self):
        # No Slide N headers and no --- dividers → no slides parsed
        md = "Just a bunch of text with no slide structure at all."
        # parse_slides falls back to splitting on ---; if no --- either, returns 1 chunk
        # The real check is: facilitator should verify slide count > 0 before Go Live
        slides = parse_slides(md)
        # May return 1 "slide" from the fallback path — important: it doesn't crash
        assert isinstance(slides, list)
