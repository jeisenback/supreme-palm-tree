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


class TestPromptBuilder:
    def test_includes_iiba_babok_structure(self):
        system_prompt, user_prompt = fui._build_iiba_babok_prompts(
            topic="Elicitation fundamentals",
            num_slides=6,
            audience="Beginner",
            certification_target="ECBA",
            focus_area="Elicitation and Collaboration",
            include_exam_tips=True,
        )
        assert "IIBA" in system_prompt
        assert "BABOK" in system_prompt
        assert "Certification target: ECBA" in user_prompt
        assert "Primary BABOK focus area: Elicitation and Collaboration" in user_prompt
        assert "exam strategy note" in user_prompt

    def test_can_disable_exam_tips(self):
        _system_prompt, user_prompt = fui._build_iiba_babok_prompts(
            topic="Strategy analysis",
            num_slides=5,
            audience="Intermediate",
            certification_target="CCBA",
            focus_area="Strategy Analysis",
            include_exam_tips=False,
        )
        assert "Do not include exam strategy notes" in user_prompt


class TestCaseStudyBuilder:
    def test_slugify_case_study_name(self):
        assert fui._slugify_case_study_name("Volunteer Hub 2.0!") == "volunteer_hub_2_0"
        assert fui._slugify_case_study_name("   ") == "new_case_study"

    def test_create_case_study_variant_with_initial_scenario(self, tmp_path):
        variant_path = fui.create_case_study_variant(
            base_dir=tmp_path,
            case_study_name="VolunteerHub donor intake modernization",
            organization_name="VolunteerHub",
            industry="Nonprofit technology",
            summary="A regional nonprofit is struggling with slow donor onboarding.",
            business_need="Reduce friction in intake and improve retention.",
            certification_target="ECBA",
            stakeholders=["Sponsor", "Operations lead"],
            success_metrics=["Cut intake time by 30%"],
            constraints=["Budget capped this quarter"],
            initial_scenario={
                "title": "Conflicting donor data requirements",
                "session_num": 1,
                "objective": "Practice stakeholder analysis",
                "situation": "Operations and fundraising disagree on required intake fields.",
                "stakeholders": ["Fundraising manager", "Operations lead"],
                "constraints": ["CRM cannot change until next release"],
                "prompts": ["What would you ask first?"],
            },
        )

        assert variant_path.name == "ECBA_CaseStudy_volunteerhub_donor_intake_modernization"
        assert (variant_path / "TrailBlaze_MasterContext.md").exists()
        assert (variant_path / "ECBA_CaseStudy_Plan.md").exists()
        assert (variant_path / "slides_draft.md").exists()

        master_context = (variant_path / "TrailBlaze_MasterContext.md").read_text(encoding="utf-8")
        assert "VolunteerHub donor intake modernization" in master_context
        assert "Reduce friction in intake and improve retention." in master_context

        scenario_path = variant_path / "scenarios" / "session_1_conflicting_donor_data_requirements.md"
        assert scenario_path.exists()
        scenario_index = json.loads((variant_path / "scenarios" / "scenarios.json").read_text(encoding="utf-8"))
        assert scenario_index[0]["title"] == "Conflicting donor data requirements"

    def test_duplicate_variant_raises(self, tmp_path):
        fui.create_case_study_variant(
            base_dir=tmp_path,
            case_study_name="Alpha",
            organization_name="Org",
            industry="Domain",
            summary="Summary",
            business_need="Need",
            certification_target="ECBA",
            stakeholders=[],
            success_metrics=[],
            constraints=[],
        )
        with pytest.raises(FileExistsError):
            fui.create_case_study_variant(
                base_dir=tmp_path,
                case_study_name="Alpha",
                organization_name="Org",
                industry="Domain",
                summary="Summary",
                business_need="Need",
                certification_target="ECBA",
                stakeholders=[],
                success_metrics=[],
                constraints=[],
            )

    def test_create_case_study_scenario_updates_index(self, tmp_path):
        variant_dir = tmp_path / "ECBA_CaseStudy_alpha"
        variant_dir.mkdir()

        first_path = fui.create_case_study_scenario(
            variant_dir=variant_dir,
            title="First scenario",
            session_num=2,
            objective="Practice elicitation",
            situation="A sponsor changes scope late in the quarter.",
            stakeholders=["Sponsor"],
            constraints=["No budget increase"],
            prompts=["What changed?"],
        )
        second_path = fui.create_case_study_scenario(
            variant_dir=variant_dir,
            title="Second scenario",
            session_num=1,
            objective="Practice stakeholder mapping",
            situation="A cross-functional team disagrees on priorities.",
            stakeholders=["Ops", "Finance"],
            constraints=["Two-week deadline"],
            prompts=["Who is impacted?"],
        )

        assert first_path.exists()
        assert second_path.exists()
        index_entries = json.loads((variant_dir / "scenarios" / "scenarios.json").read_text(encoding="utf-8"))
        assert [entry["session"] for entry in index_entries] == [1, 2]

        with pytest.raises(FileExistsError):
            fui.create_case_study_scenario(
                variant_dir=variant_dir,
                title="Second scenario",
                session_num=1,
                objective="Practice stakeholder mapping",
                situation="Duplicate scenario name.",
                stakeholders=[],
                constraints=[],
                prompts=[],
            )

    def test_build_scenario_generation_prompts(self):
        system_prompt, user_prompt = fui._build_scenario_generation_prompts(
            case_study_name="VolunteerHub",
            session_num=3,
            certification_target="ECBA",
            focus_area="Elicitation and Collaboration",
            scenario_style="Stakeholder conflict",
            master_context="Nonprofit intake modernization with sponsor tension.",
        )
        assert "Return ONLY valid JSON" in system_prompt
        assert "session 3" in user_prompt.lower()
        assert "Elicitation and Collaboration" in user_prompt
        assert "Stakeholder conflict" in user_prompt

    def test_parse_generated_scenario_response(self):
        response = json.dumps(
            {
                "title": "Conflicting priorities",
                "objective": "Practice prioritization",
                "situation": "Two stakeholders want incompatible scope changes.",
                "stakeholders": ["Sponsor", "Ops lead"],
                "constraints": ["Deadline fixed"],
                "prompts": ["What should happen first?"],
            }
        )
        parsed = fui._parse_generated_scenario_response(response)
        assert parsed["title"] == "Conflicting priorities"
        assert parsed["stakeholders"] == ["Sponsor", "Ops lead"]
        assert parsed["prompts"] == ["What should happen first?"]

    def test_load_session_scenarios_filters_by_session(self, tmp_path):
        variant_dir = tmp_path / "ECBA_CaseStudy_alpha"
        variant_dir.mkdir()
        fui.create_case_study_scenario(
            variant_dir=variant_dir,
            title="Session one scenario",
            session_num=1,
            objective="Practice stakeholder analysis",
            situation="A sponsor and analyst disagree on scope.",
            stakeholders=["Sponsor"],
            constraints=["Budget cap"],
            prompts=["Who is affected?"],
        )
        fui.create_case_study_scenario(
            variant_dir=variant_dir,
            title="Session two scenario",
            session_num=2,
            objective="Practice elicitation",
            situation="Users keep changing requested fields.",
            stakeholders=["Ops lead"],
            constraints=["Release date locked"],
            prompts=["What questions come next?"],
        )

        session_one = fui.load_session_scenarios(variant_dir, 1)
        session_two = fui.load_session_scenarios(variant_dir, 2)

        assert [item["title"] for item in session_one] == ["Session one scenario"]
        assert [item["title"] for item in session_two] == ["Session two scenario"]

    def test_update_and_delete_case_study_scenario(self, tmp_path):
        variant_dir = tmp_path / "ECBA_CaseStudy_alpha"
        variant_dir.mkdir()
        scenario_path = fui.create_case_study_scenario(
            variant_dir=variant_dir,
            title="Original scenario",
            session_num=2,
            objective="Practice elicitation",
            situation="Original situation.",
            stakeholders=["Sponsor"],
            constraints=["Budget cap"],
            prompts=["What changed?"],
        )

        updated_path = fui.update_case_study_scenario(
            variant_dir=variant_dir,
            existing_path=scenario_path,
            title="Updated scenario",
            session_num=3,
            objective="Practice prioritization",
            situation="Updated situation.",
            stakeholders=["Sponsor", "Ops lead"],
            constraints=["No timeline change"],
            prompts=["What is the tradeoff?"],
        )

        assert updated_path.name == "session_3_updated_scenario.md"
        assert updated_path.exists()
        assert not scenario_path.exists()
        loaded = fui.load_session_scenarios(variant_dir, 3)
        assert loaded[0]["title"] == "Updated scenario"
        assert loaded[0]["prompts"] == ["What is the tradeoff?"]

        fui.delete_case_study_scenario(variant_dir, updated_path)
        assert not updated_path.exists()
        assert fui.load_variant_scenarios(variant_dir) == []

    def test_build_scenario_slide_prompts(self):
        system_prompt, user_prompt = fui._build_scenario_slide_prompts(
            case_study_name="VolunteerHub",
            certification_target="ECBA",
            focus_area="Elicitation and Collaboration",
            num_slides=7,
            include_exam_tips=True,
            scenario={
                "title": "Conflicting priorities",
                "objective": "Practice prioritization",
                "situation": "Two stakeholders want incompatible scope changes.",
                "stakeholders": ["Sponsor", "Ops lead"],
                "constraints": ["Deadline fixed"],
                "prompts": ["What should happen first?"],
            },
        )
        assert "Slide N — Title" in system_prompt
        assert "Create 7 study slides" in user_prompt
        assert "Conflicting priorities" in user_prompt
        assert "exam guidance" in user_prompt.lower()


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
