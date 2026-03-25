import datetime
from pathlib import Path
import re
import os
import uuid
import json
import urllib.parse
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from facilitator_core import render_auth_sidebar
from shared import (
    SESSIONS,
    MONTH_SESSION_MAP,
    find_variants,
    find_slide_deck,
    load_master_context,
    find_preview_file,
    read_preview,
    find_documents,
    linkify_content,
    parse_slides,
    get_session_reveal,
    render_slide_body,
)


CSV_PATH = Path("etn/outputs/iiba_events_parsed.csv")
NOTES_PATH = Path("etn/outputs/facilitator_notes.csv")
LIVE_SESSION_PATH = Path("etn/outputs/session_live.json")
ATTENDEES_DIR = Path("etn/outputs/attendees")
SESSIONS_OVERRIDE_PATH = Path("etn/outputs/sessions.json")


_DESIGN_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;0,700;1,400&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
<style>
/* === Design Tokens === */
:root {
  --bg-page: #F3F4EF;
  --bg-surface: #FFFFFF;
  --bg-muted: #ECEDE6;
  --text-primary: #1F2A1F;
  --text-secondary: #4D5A4D;
  --accent-primary: #1E6B52;
  --accent-secondary: #C16A2A;
  --status-success: #237A4B;
  --status-warning: #A66400;
  --status-danger: #A12A2A;
  --border-subtle: #D4D8CC;
}

/* === Base Typography === */
html, body, [class*="css"] {
  font-family: 'Source Sans 3', 'Segoe UI', system-ui, sans-serif;
  color: var(--text-primary);
}
h1, h2, h3 {
  font-family: 'Source Serif 4', Georgia, serif;
}

/* === Slide canvas: focused reading width === */
.slide-canvas {
  max-width: 680px;
  margin: 0 auto;
}

/* === Primary button: accent green === */
.stButton > button[kind="primary"] {
  background-color: var(--accent-primary) !important;
  border-color: var(--accent-primary) !important;
  transition: background-color 150ms ease, box-shadow 150ms ease;
}
.stButton > button[kind="primary"]:hover {
  background-color: #155440 !important;
  box-shadow: 0 2px 6px rgba(30, 107, 82, 0.28);
}

/* === Subtle content transitions === */
.stMarkdown, .element-container {
  transition: opacity 200ms ease;
}

/* === Accessibility: visible focus rings === */
:focus-visible {
  outline: 2px solid var(--accent-primary) !important;
  outline-offset: 2px !important;
}
.stButton > button:focus-visible,
.stSelectbox [data-baseweb="select"]:focus-within,
.stTextInput input:focus-visible,
.stTextArea textarea:focus-visible {
  outline: 2px solid var(--accent-primary) !important;
  outline-offset: 2px !important;
}

/* === Mobile: participant join in main area === */
.join-main {
  display: none;
}
@media screen and (max-width: 768px) {
  .join-main {
    display: block;
  }
  .join-sidebar-hint {
    display: none;
  }
}
</style>
"""


def _inject_design_css():
    """Inject design tokens, typography, and accessibility CSS into the Streamlit page."""
    st.markdown(_DESIGN_CSS, unsafe_allow_html=True)


def read_live_session():
    if not LIVE_SESSION_PATH.exists():
        return None
    try:
        return json.loads(LIVE_SESSION_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        # File exists but is unreadable or malformed — surface this so it isn't
        # silently mistaken for "session not started".
        st.warning(f"session_live.json exists but could not be read ({e}). The file may be corrupt.")
        return None


def write_live_session(data: dict):
    LIVE_SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    LIVE_SESSION_PATH.write_text(json.dumps(data), encoding="utf-8")


def read_attendees() -> list:
    if not ATTENDEES_DIR.exists():
        return []
    attendees = []
    errors = 0
    for f in sorted(ATTENDEES_DIR.glob("*.json")):
        try:
            attendees.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            errors += 1
    if errors:
        st.warning(f"{errors} attendee file(s) could not be read and were skipped.")
    return attendees


def load_sessions_override() -> dict:
    """Return session overrides from sessions.json (keyed by str session number), or {}."""
    if not SESSIONS_OVERRIDE_PATH.exists():
        return {}
    try:
        return json.loads(SESSIONS_OVERRIDE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_sessions_override(overrides: dict):
    SESSIONS_OVERRIDE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_OVERRIDE_PATH.write_text(json.dumps(overrides, indent=2), encoding="utf-8")


def _call_llm(prompt: str, system: str = "") -> str:
    """Call Anthropic /v1/messages; returns text or an error string."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY environment variable is not set."
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body: dict = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]
    except Exception as e:
        return f"Error calling LLM: {e}"


def load_events():
    if CSV_PATH.exists():
        try:
            df = pd.read_csv(CSV_PATH)
        except Exception:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame(
            [
                {
                    "title": "Sample Study Session",
                    "date": "2025-06-10 19:00",
                    "format": "Virtual",
                    "link": "https://example.org/event",
                    "notes": "Sample event",
                }
            ]
        )
    return df


def save_note(event_title, facilitator, step, note, completed=False):
    NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "event_title": event_title,
        "facilitator": facilitator,
        "step": step,
        "note": note,
        "completed": bool(completed),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    df = pd.DataFrame([row])
    if NOTES_PATH.exists():
        df.to_csv(NOTES_PATH, mode="a", header=False, index=False)
    else:
        df.to_csv(NOTES_PATH, index=False)


def _generate_session_export(live: dict, attendees: list) -> str:
    """Generate a markdown export string. Snapshot semantics — reads CSV once at call time."""
    lines = [
        "# ECBA Study Session — Export",
        "",
        f"**Session ID:** {live.get('session_id', '(unknown)')}",
        f"**Started:** {live.get('started_at', '(unknown)')}",
        f"**Ended:** {live.get('ended_at', '(unknown)')}",
        "",
    ]

    lines.append(f"## Attendance ({len(attendees)} participant{'s' if len(attendees) != 1 else ''})")
    if attendees:
        name_counts: dict = {}
        for a in attendees:
            n = a.get("name", "?")
            name_counts[n] = name_counts.get(n, 0) + 1
        seen: dict = {}
        for a in attendees:
            n = a.get("name", "?")
            seen[n] = seen.get(n, 0) + 1
            display = f"{n} #{seen[n]}" if name_counts[n] > 1 else n
            lines.append(f"- {display} (joined {a.get('joined_at', '')})")
    else:
        lines.append("_(no participants recorded)_")
    lines.append("")

    lines.append("## Facilitator Notes")
    if NOTES_PATH.exists():
        try:
            df = pd.read_csv(NOTES_PATH)
            if df.empty:
                lines.append("_(no notes recorded)_")
            else:
                lines.append("| Event | Facilitator | Step | Note | Completed | Timestamp |")
                lines.append("|-------|-------------|------|------|-----------|-----------|")
                for _, row in df.iterrows():
                    def _cell(v):
                        return str(v).replace("|", "\\|") if pd.notna(v) else ""
                    lines.append(
                        f"| {_cell(row.get('event_title', ''))} "
                        f"| {_cell(row.get('facilitator', ''))} "
                        f"| {_cell(row.get('step', ''))} "
                        f"| {_cell(row.get('note', ''))} "
                        f"| {_cell(row.get('completed', ''))} "
                        f"| {_cell(row.get('timestamp', ''))} |"
                    )
        except Exception:
            lines.append("_(error reading notes)_")
    else:
        lines.append("_(no notes recorded)_")

    return "\n".join(lines)


def _do_join(name_trimmed: str):
    """Write the attendee record and set participant session state."""
    new_uuid = str(uuid.uuid4())
    existing = read_attendees()
    dup_count = sum(1 for a in existing if a.get("name") == name_trimmed)
    ATTENDEES_DIR.mkdir(parents=True, exist_ok=True)
    (ATTENDEES_DIR / f"{new_uuid}.json").write_text(
        json.dumps({
            "name": name_trimmed,
            "joined_at": datetime.datetime.utcnow().isoformat() + "Z",
            "uuid": new_uuid,
        }),
        encoding="utf-8",
    )
    st.session_state["participant_uuid"] = new_uuid
    st.session_state["participant_name"] = name_trimmed
    if dup_count > 0:
        st.toast(f"Name already in use — you've joined as {name_trimmed} #{dup_count + 1}")


def render_participant_view():
    """Participant-facing view: waiting / active (name entry + slide) / ended."""
    st.title("ECBA Study Session")
    live = read_live_session()

    if live is None:
        if LIVE_SESSION_PATH.exists():
            # File exists but read_live_session returned None → corrupt/unreadable
            st.error("Session file exists but could not be read. Please ask your facilitator to reset the session.")
        else:
            st.caption(
                "You're in the right place. "
                "The session hasn't started yet — your slide deck will appear here automatically "
                "once the facilitator goes live. No need to refresh."
            )
            st.info("Waiting for facilitator to start the session...")
        # Browser-level poll — no Streamlit flicker
        components.html('<meta http-equiv="refresh" content="5">', height=0)
        return

    if live.get("ended_at"):
        st.success("This session has ended. Thank you for attending!")
        return

    # Session is active
    p_uuid = st.session_state.get("participant_uuid")
    p_name = st.session_state.get("participant_name")

    if not p_uuid:
        # ── Desktop: join form in sidebar ────────────────────────────────────────
        with st.sidebar:
            st.markdown("### Join the session")
            name_input_sb = st.text_input("Your name", max_chars=50, key="join_name_sidebar")
            name_trimmed_sb = (name_input_sb or "").strip()
            if st.button("Join", disabled=not name_trimmed_sb, key="join_btn_sidebar"):
                _do_join(name_trimmed_sb)
                st.rerun()

        # ── Mobile: join form directly in main content area ───────────────────────
        st.markdown('<div class="join-main">', unsafe_allow_html=True)
        st.markdown("### Join the session")
        name_input_main = st.text_input("Your name", max_chars=50, key="join_name_main")
        name_trimmed_main = (name_input_main or "").strip()
        if st.button("Join", disabled=not name_trimmed_main, key="join_btn_main"):
            _do_join(name_trimmed_main)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Hint visible only on desktop (CSS hides on mobile)
        st.markdown(
            '<p class="join-sidebar-hint">Enter your name in the sidebar to join.</p>',
            unsafe_allow_html=True,
        )
        return

    # Joined — show current slide
    st.caption(f"Joined as **{p_name}**")
    live = read_live_session()  # re-read for latest slide_idx
    if live is None or live.get("ended_at"):
        st.info("Waiting for facilitator..." if live is None else "This session has ended. Thank you!")
        return

    slide_file = live.get("slide_file")
    slide_idx = live.get("slide_idx", 0)
    if slide_file:
        slide_path = Path(slide_file)
        if slide_path.exists():
            raw = slide_path.read_text(encoding="utf-8")
            slides = parse_slides(raw)
            if slides and 0 <= slide_idx < len(slides):
                s = slides[slide_idx]
                st.markdown(f"## {s['title']}")
                st.markdown(s["body"])
                st.caption(f"Slide {slide_idx + 1} of {len(slides)}")
            else:
                st.info("Waiting for first slide...")
        else:
            st.info("Waiting for slide content...")
    else:
        st.info("Waiting for slide content...")

    # Meta-refresh every 3s — browser-level, no Streamlit flicker
    components.html('<meta http-equiv="refresh" content="3">', height=0)


def _render_session_lifecycle_panel(selected_variant):
    """Session Go Live / End / Reset panel for the logged-in facilitator."""
    live = read_live_session()
    st.markdown("---")

    if live is None:
        st.markdown("#### Session: Not Started")

        # Pre-session readiness checklist — gates Go Live (#52)
        # Runs inline on every render (no caching — this is a pre-flight, not a hot path)
        slide_deck = find_slide_deck(selected_variant) if selected_variant else None
        csv_ok = CSV_PATH.exists()
        master_ok = bool(load_master_context(selected_variant))
        logged_in_ok = bool(st.session_state.get("logged_in"))
        # Check 5: Verify slide deck has parseable slides (smoke test) — catches malformed .md files
        slides_ok = bool(parse_slides(slide_deck.read_text(encoding='utf-8'))) if slide_deck else False
        all_ok = all([logged_in_ok, slide_deck is not None, csv_ok, master_ok, slides_ok])

        with st.status(
            "All checks passed — ready to go live" if all_ok else "Some checks failed — resolve before going live",
            state="complete" if all_ok else "error",
            expanded=not all_ok,
        ):
            st.write("✅ Facilitator logged in" if logged_in_ok else "❌ Facilitator not logged in")
            st.write(
                f"✅ Slide deck found: {slide_deck.name}"
                if slide_deck else "❌ Slide deck not found in variant folder"
            )
            st.write(
                "✅ Events CSV present"
                if csv_ok else "❌ Events CSV missing (etn/outputs/iiba_events_parsed.csv)"
            )
            st.write(
                "✅ Case study context loaded"
                if master_ok else "❌ Case study master context not found in variant folder"
            )
            st.write(
                "✅ Slide deck is parseable"
                if slides_ok else "❌ Slide deck has no parseable slides (malformed .md?)"
            )

        if st.button("Go Live", type="primary", key="go_live_btn", disabled=not all_ok):
            write_live_session({
                "session_id": str(uuid.uuid4()),
                "slide_idx": 0,
                "slide_file": str(slide_deck).replace("\\", "/") if slide_deck else "",
                "started_at": datetime.datetime.utcnow().isoformat() + "Z",
                "ended_at": None,
            })
            st.success("Session started! Share the app URL with participants (no ?facilitator=1).")
            st.rerun()
        st.markdown("---")
        return

    if live.get("ended_at"):
        st.markdown(f"#### Session: Ended — {live.get('ended_at', '')}")

        # Post-session export (#53)
        export_md = st.session_state.get("_export_md")
        if not export_md:
            # Fallback: regenerate if session_state was lost (e.g. page refresh)
            if st.button("Generate Export", key="regen_export_btn"):
                st.session_state["_export_md"] = _generate_session_export(live, read_attendees())
                st.session_state["_export_session_id"] = live.get("session_id", "session")[:8]
                st.rerun()
        else:
            session_id_short = st.session_state.get("_export_session_id", "session")
            st.download_button(
                "Download Session Export (.md)",
                data=export_md.encode("utf-8"),
                file_name=f"session_export_{session_id_short}.md",
                mime="text/markdown",
                key="download_export_btn",
            )

        if not st.session_state.get("_reset_confirm"):
            if st.button("Reset Session", key="reset_btn"):
                st.session_state["_reset_confirm"] = True
                st.rerun()
        else:
            st.error("This will permanently delete all attendance records and session data.")
            confirm_text = st.text_input(
                "Type RESET to confirm",
                key="reset_confirm_text",
                placeholder="RESET",
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button(
                    "Reset", key="reset_yes",
                    disabled=(confirm_text or "").strip() != "RESET",
                ):
                    LIVE_SESSION_PATH.unlink(missing_ok=True)
                    if ATTENDEES_DIR.exists():
                        for f in ATTENDEES_DIR.glob("*.json"):
                            f.unlink(missing_ok=True)
                    st.session_state.pop("_reset_confirm", None)
                    st.session_state.pop("reset_confirm_text", None)
                    st.rerun()
            with c2:
                if st.button("Cancel", key="reset_cancel"):
                    st.session_state.pop("_reset_confirm", None)
                    st.rerun()
        st.markdown("---")
        return

    # Active session — headcount + End Session
    attendees = read_attendees()
    count = len(attendees)
    c_status, c_actions = st.columns([3, 2])
    with c_status:
        st.markdown(
            f"#### Session: **Live** — {count} participant{'s' if count != 1 else ''} joined"
        )
        st.caption(f"Started {live.get('started_at', '')}")
        if attendees:
            name_counts: dict = {}
            for a in attendees:
                n = a.get("name", "?")
                name_counts[n] = name_counts.get(n, 0) + 1
            seen: dict = {}
            names = []
            for a in attendees:
                n = a.get("name", "?")
                seen[n] = seen.get(n, 0) + 1
                names.append(f"{n} #{seen[n]}" if name_counts[n] > 1 else n)
            st.markdown("**Roster:** " + ", ".join(names))
    with c_actions:
        if st.button("End Session", type="primary", key="end_session_btn"):
            # Snapshot notes + roster at click time, then set ended_at (#53)
            # Single-writer facilitator: no file locking needed for notes CSV
            ended_at = datetime.datetime.utcnow().isoformat() + "Z"
            live["ended_at"] = ended_at
            export_md = _generate_session_export(live, attendees)
            write_live_session(live)
            st.session_state["_export_md"] = export_md
            st.session_state["_export_session_id"] = live.get("session_id", "session")[:8]
            st.rerun()

    # Meta-refresh every 5s for headcount updates (browser-level)
    components.html('<meta http-equiv="refresh" content="5">', height=0)
    st.markdown("---")


def _validate_practice_questions(pq_list) -> list:
    """Validate practice questions structure. Returns list of error strings."""
    if not isinstance(pq_list, list):
        return ["must be a JSON array"]
    errors = []
    for i, item in enumerate(pq_list):
        prefix = f"Question {i + 1}"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: must be an object {{q, choices, a}}")
            continue
        if "q" not in item:
            errors.append(f"{prefix}: missing 'q' (question text)")
        elif not isinstance(item["q"], str):
            errors.append(f"{prefix}: 'q' must be a string")
        if "choices" not in item:
            errors.append(f"{prefix}: missing 'choices' (list of options)")
        elif not isinstance(item["choices"], list) or len(item["choices"]) < 2:
            errors.append(f"{prefix}: 'choices' must be an array with \u2265 2 items")
        if "a" not in item:
            errors.append(f"{prefix}: missing 'a' (correct answer index, 0-based)")
        elif not isinstance(item["a"], int):
            errors.append(f"{prefix}: 'a' must be an integer index")
        elif "choices" in item and isinstance(item["choices"], list):
            if not (0 <= item["a"] < len(item["choices"])):
                errors.append(
                    f"{prefix}: 'a' = {item['a']} is out of range "
                    f"(valid: 0\u2013{len(item['choices']) - 1})"
                )
    return errors


def _render_content_authoring(session_num: int, selected_variant):
    """Content authoring module — sessions editor, AI draft generator, slide upload (#55)."""
    st.subheader("Content Authoring")
    tab_editor, tab_ai, tab_upload = st.tabs(
        ["Sessions Editor", "AI Draft Generator", "Slide Upload"]
    )

    # ── Sessions Editor ──────────────────────────────────────────────────────────
    with tab_editor:
        st.markdown(
            "Edit session content. Changes are saved to `etn/outputs/sessions.json` "
            "and override the defaults in `shared.py`."
        )
        overrides = load_sessions_override()
        # Load current values: override → SESSIONS fallback
        base = dict(SESSIONS.get(session_num, {}))
        current = dict(overrides.get(str(session_num), base))

        title = st.text_input("Title", value=current.get("title", ""), key="edit_title")
        agenda_raw = st.text_area(
            "Agenda (one item per line)",
            value="\n".join(current.get("agenda", [])),
            height=120,
            key="edit_agenda",
        )
        homework = st.text_input("Homework", value=current.get("homework", ""), key="edit_hw")
        prompts_raw = st.text_area(
            "Discussion prompts (one per line)",
            value="\n".join(current.get("prompts", [])),
            height=80,
            key="edit_prompts",
        )

        # ── Guided Practice Question Form ─────────────────────────────────────────
        st.markdown("**Practice questions**")
        # Per-session state key avoids stale data when user switches sessions
        pq_state_key = f"_pq_guided_list_{session_num}"
        if pq_state_key not in st.session_state:
            st.session_state[pq_state_key] = list(current.get("practice_questions", []))

        advanced_mode = st.toggle("Advanced mode (edit raw JSON)", key="pq_advanced_mode")

        if advanced_mode:
            pq_default = json.dumps(st.session_state[pq_state_key], indent=2)
            pq_raw = st.text_area(
                "Practice questions JSON",
                value=pq_default,
                height=160,
                key="edit_pq_raw",
                help='Each item: {"q": "...", "choices": ["A", "B", "C", "D"], "a": 0}',
            )
            try:
                _pq_preview = json.loads(pq_raw)
                if isinstance(_pq_preview, list):
                    st.caption(f"{len(_pq_preview)} question(s) in JSON.")
            except Exception:
                st.warning("JSON syntax error — fix before saving.")
        else:
            existing_questions = st.session_state[pq_state_key]
            if existing_questions:
                for i, q in enumerate(existing_questions):
                    cols = st.columns([8, 1])
                    with cols[0]:
                        choice_lines = "  \n".join(
                            f"{'✓' if j == q.get('a') else '○'} {c}"
                            for j, c in enumerate(q.get("choices", []))
                        )
                        st.markdown(f"**Q{i + 1}.** {q.get('q', '')}  \n{choice_lines}")
                    with cols[1]:
                        if st.button("✕", key=f"pq_del_{i}", help="Remove this question"):
                            st.session_state[pq_state_key].pop(i)
                            st.rerun()
            else:
                st.caption("No practice questions yet.")

            st.markdown("**Add a question**")
            with st.form(f"pq_add_form_{session_num}", clear_on_submit=True):
                stem = st.text_input("Question stem", key="pq_stem")
                c_cols = st.columns(2)
                with c_cols[0]:
                    choice_a = st.text_input("Choice A", key="pq_ca")
                    choice_b = st.text_input("Choice B", key="pq_cb")
                with c_cols[1]:
                    choice_c = st.text_input("Choice C", key="pq_cc")
                    choice_d = st.text_input("Choice D", key="pq_cd")
                correct = st.selectbox("Correct answer", ["A", "B", "C", "D"], key="pq_correct")
                submitted = st.form_submit_button("Add question")
                if submitted:
                    choices = [c for c in [choice_a, choice_b, choice_c, choice_d] if c.strip()]
                    if not stem.strip():
                        st.error("Question stem is required.")
                    elif len(choices) < 2:
                        st.error("Provide at least 2 choices.")
                    else:
                        answer_idx = {"A": 0, "B": 1, "C": 2, "D": 3}[correct]
                        if answer_idx >= len(choices):
                            answer_idx = 0
                        st.session_state[pq_state_key].append(
                            {"q": stem.strip(), "choices": choices, "a": answer_idx}
                        )
                        st.rerun()

        if st.button("Save session content", key="save_session_content"):
            if advanced_mode:
                try:
                    pq_parsed = json.loads(st.session_state.get("edit_pq_raw", "[]"))
                except Exception as e:
                    st.error(f"Practice questions JSON is invalid: {e}")
                    return
                # Sync back to guided list for consistency
                st.session_state[pq_state_key] = pq_parsed if isinstance(pq_parsed, list) else []
            else:
                pq_parsed = st.session_state[pq_state_key]
            pq_errors = _validate_practice_questions(pq_parsed)
            if pq_errors:
                st.error("Practice questions schema errors — fix before saving:")
                for err in pq_errors:
                    st.write(f"- {err}")
                return
            updated = {
                "title": title,
                "agenda": [l.strip() for l in agenda_raw.splitlines() if l.strip()],
                "homework": homework,
                "prompts": [l.strip() for l in prompts_raw.splitlines() if l.strip()],
                "practice_questions": pq_parsed,
            }
            overrides[str(session_num)] = updated
            save_sessions_override(overrides)
            st.success(f"Session {session_num} saved to sessions.json.")

        if overrides.get(str(session_num)):
            if st.button("Reset to defaults", key="reset_session_content"):
                overrides.pop(str(session_num), None)
                save_sessions_override(overrides)
                # Clear guided-mode cache so it reloads defaults on next render
                st.session_state.pop(pq_state_key, None)
                st.success("Reset to shared.py defaults.")
                st.rerun()

    # ── AI Draft Generator ────────────────────────────────────────────────────────
    with tab_ai:
        st.markdown(
            "Generate slide deck content using AI. Describe your topic and the output "
            "will be formatted for `parse_slides` (Slide N headers)."
        )
        topic = st.text_input(
            "Topic / objective",
            placeholder="e.g. 'BACCM core concepts for ECBA exam prep, Session 1'",
            key="ai_topic",
        )
        num_slides = st.slider("Number of slides", 3, 20, 8, key="ai_num_slides")
        audience = st.selectbox(
            "Audience level", ["Beginner", "Intermediate", "Advanced"], key="ai_audience"
        )

        if st.button("Generate draft", key="ai_generate", disabled=not topic.strip()):
            system_prompt = (
                "You are a content author creating training slides for a professional "
                "development study session. Output ONLY the slide content in markdown format. "
                "Use 'Slide N — Title' headers (e.g. 'Slide 1 — Introduction'). "
                "Each slide should have body content and optionally a [FACILITATOR: note] block. "
                "No preamble, no explanation — just the slides."
            )
            user_prompt = (
                f"Create {num_slides} slides on: {topic.strip()}\n"
                f"Audience: {audience} level. "
                "Each slide: title, 3-5 bullet points, optional facilitator note."
            )
            with st.spinner("Generating..."):
                result = _call_llm(user_prompt, system=system_prompt)
            st.session_state["_ai_draft"] = result

        draft = st.session_state.get("_ai_draft", "")
        if draft:
            edited = st.text_area(
                "Generated draft (edit before saving)",
                value=draft,
                height=400,
                key="ai_draft_edit",
            )

            # ── Preview as slides ────────────────────────────────────────────────
            with st.expander("Preview slides", expanded=False):
                slides_preview = parse_slides(edited)
                if slides_preview:
                    st.caption(f"{len(slides_preview)} slide(s) parsed.")
                    for s in slides_preview:
                        slide_title = s.get("title", "(untitled)")
                        body_lines = (s.get("body") or "").strip().splitlines()
                        first_line = body_lines[0] if body_lines else "_no content_"
                        st.markdown(f"**{slide_title}** — {first_line}")
                else:
                    st.warning(
                        "No slides parsed. Check that headers use 'Slide N — Title' format."
                    )

            # ── Validate ─────────────────────────────────────────────────────────
            slides_validated = parse_slides(edited)
            if not slides_validated:
                st.warning(
                    "Draft has no parseable slides — fix headers before saving."
                )
                save_ok = False
            else:
                st.success(f"Validated: {len(slides_validated)} slide(s) ready.")
                save_ok = True

            # ── Save as draft / Publish ───────────────────────────────────────────
            if selected_variant and save_ok:
                col_save, col_pub = st.columns(2)
                with col_save:
                    if st.button(
                        "Save as draft",
                        key="ai_save_draft",
                        help="Save to slides_draft.md in the variant folder",
                    ):
                        dest = Path(selected_variant) / "slides_draft.md"
                        dest.write_text(edited, encoding="utf-8")
                        st.success(f"Draft saved to {dest}")
                        find_slide_deck.clear()
                        find_documents.clear()
                with col_pub:
                    active_deck = find_slide_deck(selected_variant)
                    if active_deck:
                        if st.button(
                            "Publish to active deck",
                            key="ai_publish_deck",
                            type="primary",
                            help=f"Overwrite {active_deck.name} with this draft",
                        ):
                            active_deck.write_text(edited, encoding="utf-8")
                            st.success(f"Published to {active_deck}")
                            find_slide_deck.clear()
                            find_documents.clear()
                    else:
                        st.info(
                            "No active slide deck found in this variant folder. "
                            "Save as draft first, then rename it to activate."
                        )
            elif not selected_variant:
                st.info("Select a case study variant to enable saving.")

    # ── Slide Upload ──────────────────────────────────────────────────────────────
    with tab_upload:
        st.markdown(
            "Upload a `.md` or `.txt` slide deck file to replace the current deck "
            "in the selected variant folder."
        )
        if not selected_variant:
            st.warning("Select a case study variant first.")
        else:
            uploaded = st.file_uploader(
                "Choose slide deck file",
                type=["md", "txt"],
                key="slide_upload_file",
            )
            if uploaded is not None:
                dest_name = st.text_input(
                    "Save as filename",
                    value=uploaded.name,
                    key="slide_upload_dest",
                )
                dest = Path(selected_variant) / dest_name
                if dest.exists():
                    existing_text = dest.read_text(encoding="utf-8")
                    new_text = uploaded.getvalue().decode("utf-8", errors="replace")
                    existing_lines = existing_text.splitlines()
                    new_lines = new_text.splitlines()
                    st.warning(
                        f"**File already exists.** "
                        f"Current: {len(existing_lines)} line(s) · "
                        f"New: {len(new_lines)} line(s)"
                    )
                    for i, (old_line, new_line) in enumerate(
                        zip(existing_lines, new_lines)
                    ):
                        if old_line != new_line:
                            st.caption(
                                f"First difference at line {i + 1}: "
                                f"`{old_line[:60]}` → `{new_line[:60]}`"
                            )
                            break
                    backup = st.checkbox(
                        f"Backup existing file to `{dest_name}.bak` (recommended)",
                        value=True,
                        key="slide_upload_backup",
                    )
                    if st.button("Confirm replace", key="slide_upload_confirm", type="primary"):
                        if backup:
                            bak = dest.with_suffix(dest.suffix + ".bak")
                            bak.write_text(existing_text, encoding="utf-8")
                            st.info(f"Backup saved to {bak.name}")
                        dest.write_bytes(uploaded.getvalue())
                        st.success(f"Replaced {dest}")
                        find_slide_deck.clear()
                        find_documents.clear()
                else:
                    if st.button("Upload and save", key="slide_upload_save"):
                        dest.write_bytes(uploaded.getvalue())
                        st.success(f"Saved to {dest}")
                        find_slide_deck.clear()
                        find_documents.clear()


def main():
    _is_facilitator = st.query_params.get("facilitator") == "1"
    st.set_page_config(
        page_title="ECBA Study Session — Facilitator" if _is_facilitator else "ECBA Study Session",
        layout="wide",
    )
    _inject_design_css()

    if not _is_facilitator:
        render_participant_view()
        return

    st.title("ECBA Study Session — Facilitator")

    # Ensure facilitator is always defined (guards Notes/Actions/Complete steps)
    facilitator = st.session_state.get("facilitator", "")

    events = load_events()
    if events.empty:
        st.warning("No events found in etn/outputs/iiba_events_parsed.csv — using sample data.")

    titles = events.get("title", events.get("Title", events.columns.tolist())).tolist()
    if not titles:
        titles = ["(no events)"]

    with st.sidebar:
        facilitator = render_auth_sidebar()
        # Update local var in case auto-login ran during sidebar render
        facilitator = st.session_state.get("facilitator", "")
        st.markdown("---")
        event_choice = st.selectbox("Select event", titles)
        STEPS = ["Overview", "Discussion prompts", "Notes", "Actions", "Complete", "Case Study"]
        st.markdown("---")
        # Session status — always visible regardless of scroll position
        _live_sidebar = read_live_session()
        if _live_sidebar and not _live_sidebar.get("ended_at"):
            st.success("Session Live")
        elif _live_sidebar and _live_sidebar.get("ended_at"):
            st.warning("Session Ended")
        else:
            st.caption("Session not started")
        st.markdown("---")
        step = st.radio("Step", STEPS, key="radio_step")

    st.header(event_choice)

    # Variant selector
    variants = find_variants()
    variant_names = [p.name for p in variants]
    selected_variant = None
    if not variant_names:
        variant_names = ["ECBA_CaseStudy (not found)"]
    else:
        sel = st.sidebar.selectbox("Case study variant", variant_names, index=0)
        selected_variant = variants[variant_names.index(sel)]

    st.sidebar.markdown("**Variant folder:**")
    st.sidebar.write(str(selected_variant) if selected_variant is not None else "(none)")

    if st.session_state.get("logged_in"):
        _render_session_lifecycle_panel(selected_variant)

    master_text = load_master_context(selected_variant)

    preview_path = find_preview_file(selected_variant)
    preview_text = read_preview(preview_path)
    with st.expander("Variant overview"):
        if preview_path:
            st.markdown(f"**Preview file:** {preview_path.name}")
            st.markdown(preview_text)
        else:
            st.info("No plan or README found to preview in this variant folder.")

    docs = find_documents(selected_variant)
    params = st.query_params
    open_param = params.get("open")
    presenter_param = params.get("presenter")
    slide_param = params.get("slide")
    timer_param = params.get("timer")
    open_path = None

    if not open_param and preview_path:
        open_path = preview_path
        open_param = str(preview_path)
    if open_param:
        try:
            possible = Path(urllib.parse.unquote(open_param))
            if not possible.is_absolute():
                possible = Path(possible)
            if possible.exists():
                open_path = possible
            else:
                if selected_variant:
                    candidate = selected_variant.joinpath(
                        urllib.parse.unquote(open_param)
                    ).resolve()
                    if candidate.exists():
                        open_path = candidate
        except Exception:
            open_path = None

    with st.expander("Documents"):
        if docs:
            for p in docs:
                rel = str(p).replace("\\", "/")
                link = f"?open={urllib.parse.quote(rel)}"
                st.markdown(f"- [{p.name}]({link})  ")
        else:
            st.info("No documents found in this variant folder.")

    if open_path and open_path.exists():
        st.markdown("---")
        st.subheader(f"Viewing: {open_path.name}")
        try:
            raw = open_path.read_text(encoding="utf-8")
        except Exception:
            raw = "(binary or unreadable file)"

        is_slide_deck = False
        if "slide" in open_path.name.lower() or "slides" in open_path.name.lower():
            is_slide_deck = True
        if not is_slide_deck and isinstance(raw, str) and re.search(
            r"(?m)^Slide\s+\d+\b", raw
        ):
            is_slide_deck = True

        if is_slide_deck and open_path.suffix.lower() in (".md", ".txt"):
            slides = parse_slides(raw)
            if not slides:
                st.markdown("(no slides parsed)")
            else:
                safe_open = str(open_path).replace("\\", "_").replace("/", "_")
                key_idx = f"slide_idx_{safe_open}"
                if key_idx not in st.session_state:
                    st.session_state[key_idx] = 0

                try:
                    if slide_param is not None:
                        sval = int(slide_param)
                        if 0 <= sval < len(slides):
                            st.session_state[key_idx] = sval
                except Exception:
                    pass

                idx = st.session_state[key_idx]

                # Sync current slide to live session when facilitator navigates
                _live = read_live_session()
                if (
                    _live and not _live.get("ended_at")
                    and open_path is not None
                    and str(open_path).replace("\\", "/") == (_live.get("slide_file") or "").replace("\\", "/")
                    and _live.get("slide_idx") != idx
                ):
                    _live["slide_idx"] = idx
                    try:
                        write_live_session(_live)
                    except Exception as _e:
                        st.warning(f"Could not sync slide to participants: {_e}")

                if presenter_param and presenter_param.lower() in ("1", "true", "yes"):
                    st.markdown(
                        "**Presenter View — open in a separate window for presenting**"
                    )
                    pcol_main, pcol_side = st.columns([8, 3])
                    with pcol_main:
                        s = slides[idx]
                        st.markdown(f"# {s['title']}")
                        rendered = render_slide_body(s["body"], docs, selected_variant)
                        st.markdown(rendered, unsafe_allow_html=False)
                        nav1, nav2, nav3 = st.columns([1, 1, 6])
                        with nav1:
                            if st.button("Previous"):
                                st.session_state[key_idx] = max(
                                    0, st.session_state[key_idx] - 1
                                )
                                st.rerun()
                        with nav2:
                            if st.button("Next"):
                                st.session_state[key_idx] = min(
                                    len(slides) - 1, st.session_state[key_idx] + 1
                                )
                                st.rerun()

                        progress = int((idx + 1) / max(1, len(slides)) * 100)
                        st.progress(progress)

                        open_enc = urllib.parse.quote(
                            str(open_path).replace("\\", "/")
                        )
                        js = """
                        <div>
                          <label>Auto-advance interval (seconds):</label>
                          <input id='interval' type='number' min='1' value='10' style='width:80px' />
                          <button id='start_btn'>Start</button>
                          <button id='stop_btn'>Stop</button>
                        </div>
                        <script>
                        (function(){{
                          let timer = null;
                          function getParam(name){{
                            const params = new URLSearchParams(window.location.search);
                            return params.get(name);
                          }}
                          function setSlide(n){{
                            const params = new URLSearchParams(window.location.search);
                            params.set('open','__OPEN_ENC__');
                            params.set('presenter','true');
                            params.set('slide', String(n));
                            window.location.search = params.toString();
                          }}
                          document.getElementById('start_btn').addEventListener('click', function(){{
                            const iv = parseInt(document.getElementById('interval').value || '10');
                            let cur = parseInt(getParam('slide') || '__IDX__');
                            if(timer) clearInterval(timer);
                            timer = setInterval(function(){{
                              cur = Math.min(cur + 1, __MAXIDX__);
                              setSlide(cur);
                              if(cur >= __MAXIDX__) clearInterval(timer);
                            }}, iv*1000);
                          }});
                          document.getElementById('stop_btn').addEventListener('click', function(){{
                            if(timer) clearInterval(timer);
                          }});
                          document.addEventListener('keydown', function(e){{
                            if(e.key === 'ArrowRight'){{
                              let cur = parseInt(getParam('slide') || '__IDX__');
                              setSlide(Math.min(cur+1, __MAXIDX__));
                            }} else if(e.key === 'ArrowLeft'){{
                              let cur = parseInt(getParam('slide') || '__IDX__');
                              setSlide(Math.max(cur-1, 0));
                            }}
                          }});
                        }})();
                        </script>
                        """
                        js = js.replace("__OPEN_ENC__", open_enc)
                        js = (
                            js.replace("__IDX__", str(idx))
                            .replace("__MAXIDX__", str(len(slides) - 1))
                        )
                        components.html(js, height=120)

                    with pcol_side:
                        st.markdown("**Facilitator notes**")
                        s = slides[idx]
                        if s["facilitator_notes"]:
                            for n in s["facilitator_notes"]:
                                st.write(n)
                        else:
                            st.write("(no notes)")

                        st.markdown("---")
                        # Timer panel: T key toggles ?timer=1 (show) / ?timer=0 (hide) (#54)
                        # Always init state so running timer survives hide/show cycles
                        tkey = f"timer_{key_idx}_{safe_open}"
                        if tkey not in st.session_state:
                            st.session_state[tkey] = {
                                "running": False,
                                "end": None,
                                "remaining": 0,
                            }

                        if timer_param != "1":
                            st.caption("Press **T** to show timer")
                        else:
                            st.markdown("**Timer** *(press T to hide)*")
                            minutes = st.number_input(
                                "Minutes",
                                min_value=0,
                                max_value=180,
                                value=10,
                                step=1,
                                key=f"min_{tkey}",
                            )
                            if st.button("Start", key=f"start_{tkey}"):
                                st.session_state[tkey]["running"] = True
                                st.session_state[tkey]["end"] = (
                                    time.time() + int(minutes) * 60
                                )
                                st.session_state[tkey]["remaining"] = int(minutes) * 60
                                st.rerun()
                            if st.button("Pause", key=f"pause_{tkey}"):
                                if (
                                    st.session_state[tkey]["running"]
                                    and st.session_state[tkey]["end"]
                                ):
                                    st.session_state[tkey]["remaining"] = max(
                                        0,
                                        int(st.session_state[tkey]["end"] - time.time()),
                                    )
                                    st.session_state[tkey]["running"] = False
                                    st.session_state[tkey]["end"] = None
                            if st.button("Reset", key=f"reset_{tkey}"):
                                st.session_state[tkey] = {
                                    "running": False,
                                    "end": None,
                                    "remaining": int(minutes) * 60,
                                }
                                st.rerun()

                            # JS-based timer display — no server-side sleep
                            if st.session_state[tkey]["running"] and st.session_state[tkey]["end"]:
                                remaining = int(st.session_state[tkey]["end"] - time.time())
                                if remaining <= 0:
                                    st.warning("Time's up")
                                    st.session_state[tkey]["running"] = False
                                    st.session_state[tkey]["end"] = None
                                    st.session_state[tkey]["remaining"] = 0
                                else:
                                    end_ts = int(st.session_state[tkey]["end"] * 1000)
                                    timer_js = f"""
                                    <div id='timer_display' style='font-size:2rem;font-weight:bold'></div>
                                    <script>
                                    (function(){{
                                      const endMs = {end_ts};
                                      function update(){{
                                        const rem = Math.max(0, Math.round((endMs - Date.now()) / 1000));
                                        const m = String(Math.floor(rem/60)).padStart(2,'0');
                                        const s = String(rem%60).padStart(2,'0');
                                        document.getElementById('timer_display').textContent = m+':'+s;
                                        if(rem > 0) setTimeout(update, 500);
                                        else document.getElementById('timer_display').style.color='red';
                                      }}
                                      update();
                                    }})();
                                    </script>
                                    """
                                    components.html(timer_js, height=60)
                            else:
                                rem = st.session_state[tkey].get("remaining", 0)
                                mins = rem // 60
                                secs = rem % 60
                                st.markdown(f"## {mins:02d}:{secs:02d}")

                        st.markdown("---")
                        st.markdown("Open audience view:")
                        aud_rel = urllib.parse.quote(str(open_path).replace("\\", "/"))
                        st.markdown(f"[Open audience view](?open={aud_rel})")

                else:
                    col1, col2, col3 = st.columns([1, 6, 2])
                    with col1:
                        if st.button("Previous"):
                            st.session_state[key_idx] = max(
                                0, st.session_state[key_idx] - 1
                            )
                            st.rerun()
                        if st.button("Next"):
                            st.session_state[key_idx] = min(
                                len(slides) - 1, st.session_state[key_idx] + 1
                            )
                            st.rerun()
                        st.write(f"{idx+1}/{len(slides)}")
                        st.slider(
                            "Jump to",
                            1,
                            len(slides),
                            idx + 1,
                            key=f"slider_{key_idx}",
                            on_change=lambda: st.session_state.update(
                                {key_idx: st.session_state[f"slider_{key_idx}"] - 1}
                            ),
                        )

                    with col2:
                        s = slides[idx]
                        st.markdown(f"### {s['title']}")
                        presenter_mode = st.checkbox(
                            "Presenter mode",
                            value=st.session_state.get("presenter_mode", False),
                        )
                        st.session_state["presenter_mode"] = presenter_mode

                        if presenter_mode:
                            # JS-based auto-advance — no server-side sleep
                            auto = st.checkbox(
                                "Auto-advance",
                                value=st.session_state.get("auto_advance", False),
                            )
                            st.session_state["auto_advance"] = auto
                            interval = st.slider("Interval (seconds)", 2, 60, value=10)
                            st.session_state["auto_interval"] = interval
                            if auto:
                                open_enc = urllib.parse.quote(
                                    str(open_path).replace("\\", "/")
                                )
                                auto_js = f"""
                                <script>
                                (function(){{
                                  const iv = {interval} * 1000;
                                  const maxIdx = {len(slides) - 1};
                                  let cur = {idx};
                                  setTimeout(function advance(){{
                                    cur = Math.min(cur + 1, maxIdx);
                                    const p = new URLSearchParams(window.location.search);
                                    p.set('open','{open_enc}');
                                    p.set('slide', String(cur));
                                    window.location.search = p.toString();
                                  }}, iv);
                                }})();
                                </script>
                                """
                                components.html(auto_js, height=0)

                        rendered = render_slide_body(
                            s["body"], docs, selected_variant
                        )
                        st.markdown(rendered, unsafe_allow_html=False)

                    with col3:
                        show_notes = st.checkbox("Show facilitator notes", value=True)
                        if show_notes and s["facilitator_notes"]:
                            st.markdown("**Facilitator notes:**")
                            for n in s["facilitator_notes"]:
                                st.write(n)

                    pq = [p for p in docs if "PracticeQuestions" in p.name]
                    if pq:
                        st.markdown("---")
                        st.markdown("**Practice question sets:**")
                        for p in pq:
                            rel = str(p).replace("\\", "/")
                            st.markdown(
                                f"- [{p.name}](?open={urllib.parse.quote(rel)})"
                            )

        else:
            if open_path.suffix.lower() in (".md", ".txt"):
                linked = linkify_content(raw, docs)
                st.markdown(linked, unsafe_allow_html=False)
            else:
                st.download_button(
                    "Download file",
                    data=open_path.read_bytes(),
                    file_name=open_path.name,
                )

    # Auto-select session based on current month, allow manual override
    now = datetime.datetime.now()
    default_session = MONTH_SESSION_MAP.get(now.month)
    session_selected = st.sidebar.selectbox(
        "Session (auto-selected by month)",
        ["Auto-select"] + [f"Session {i}" for i in range(1, 6)],
        index=0,
    )
    if session_selected == "Auto-select":
        session_num = default_session or 1
    else:
        session_num = int(session_selected.split()[1])

    session = SESSIONS.get(session_num)
    # Apply session content overrides from sessions.json if present (#55)
    _session_overrides = load_sessions_override()
    if str(session_num) in _session_overrides:
        session = _session_overrides[str(session_num)]

    st.markdown("---")
    st.subheader(session["title"])
    st.markdown("**Agenda:**")
    for item in session["agenda"]:
        st.write(f"- {item}")
    st.markdown("**Homework:**")
    st.write(session["homework"])
    st.markdown("**Prompts:**")
    for p in session["prompts"]:
        st.write(f"- {p}")

    st.markdown("**Practice questions:**")
    for i, q in enumerate(session["practice_questions"]):
        st.write(f"{i+1}. {q['q']}")
        choice = st.radio(f"Question {i+1}", q["choices"], key=f"q_{session_num}_{i}")
        if st.button(f"Check answer {i+1}", key=f"check_{session_num}_{i}"):
            correct = q["choices"][q["a"]]
            if choice == correct:
                st.success("Correct")
            else:
                st.error(f"Incorrect — correct answer: {correct}")

    # Case study gating UI
    if step == "Case Study":
        st.subheader("Case Study — TrailBlaze Master Context (facilitator only)")
        if not master_text:
            st.warning("TrailBlaze_MasterContext.md not found in etn/ECBA_CaseStudy/")
        st.markdown(
            "**Warning:** This document contains session-gated reveals. "
            "Do not distribute to participants."
        )
        confirm = st.checkbox(
            "I confirm I am the facilitator and will not share reveals with participants"
        )
        session_select = st.selectbox(
            "Select session reveal to view",
            [
                "Full document",
                "SESSION 1 REVEAL",
                "SESSION 2 REVEAL",
                "SESSION 3 REVEAL",
                "SESSION 4 REVEAL",
                "SESSION 5 REVEAL",
            ],
        )
        if confirm:
            if session_select == "Full document":
                st.markdown("---")
                st.markdown(master_text)
            else:
                reveal = get_session_reveal(master_text, session_select)
                st.markdown("---")
                st.markdown(reveal)
        else:
            st.info("Check the confirmation box to reveal gated content.")

    # Show event details if available
    if event_choice != "(no events)":
        row = events[
            events.get("title", events.get("Title", "title")) == event_choice
        ]
        if not row.empty:
            r = row.iloc[0].to_dict()
            st.markdown(f"**Date:** {r.get('date') or r.get('Date') or ''}")
            st.markdown(f"**Format:** {r.get('format') or r.get('Format') or ''}")
            link = r.get("link") or r.get("Link") or ""
            if link:
                st.markdown(f"**Link:** <{link}>", unsafe_allow_html=True)
            st.write(r.get("notes") or r.get("Notes") or "")

    st.subheader(step)

    if step == "Overview":
        st.write("Follow the event summary, goals, and desired outcomes.")
        if st.button("Start discussion"):
            st.rerun()

    if step == "Discussion prompts":
        for prompt in session["prompts"]:
            st.write(f"- {prompt}")

    if step == "Notes":
        if not st.session_state.get("logged_in"):
            st.info("Please log in to save notes.")
        else:
            key = f"note_{event_choice}_{step}"
            note = st.text_area("Notes", value=st.session_state.get(key, ""), height=200)
            st.session_state[key] = note
            if st.button("Save note"):
                save_note(event_choice, facilitator, step, note)
                st.success("Saved")

    if step == "Actions":
        if not st.session_state.get("logged_in"):
            st.info("Please log in to save action items.")
        else:
            action = st.text_input("Action item")
            owner = st.text_input("Owner")
            due = st.date_input("Due date")
            if st.button("Save action"):
                save_note(
                    event_choice,
                    facilitator,
                    step,
                    f"Action: {action}; Owner: {owner}; Due: {due}",
                )
                st.success("Action saved")

    if step == "Complete":
        if not st.session_state.get("logged_in"):
            st.info("Please log in to finalize the session.")
        else:
            completed = st.checkbox("Mark session complete")
            if st.button("Finalize"):
                save_note(event_choice, facilitator, step, "Finalized", completed=completed)
                st.success("Session finalized")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"Notes saved: {NOTES_PATH.name if NOTES_PATH.exists() else 'none'}"
    )


if __name__ == "__main__":
    main()
