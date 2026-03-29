import datetime
from pathlib import Path
import re
import os
import uuid
import json
import requests
import urllib.parse
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from brand import BRAND_CSS
from frontmatter_utils import read_frontmatter
from shared import (
    SESSIONS,
    MONTH_SESSION_MAP,
    find_variants,
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
SESSION_PATH = Path("etn/outputs/facilitator_session.json")


def save_persistent_session(name: str, token: str, expires_iso: str):
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"name": name, "token": token, "expires": expires_iso}
    SESSION_PATH.write_text(json.dumps(payload), encoding="utf-8")


def load_persistent_session():
    if not SESSION_PATH.exists():
        return None
    try:
        data = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
        return data
    except Exception:
        return None


def clear_persistent_session():
    try:
        if SESSION_PATH.exists():
            SESSION_PATH.unlink()
    except Exception:
        pass


_PROJECT_ROOT = Path(__file__).parent.parent
_PANEL_EVENT_DIR = _PROJECT_ROOT / "etn" / "templates" / "panel_event"


def _is_published(path: Path) -> bool:
    """Return True if file is published or has no frontmatter (legacy file)."""
    meta, _ = read_frontmatter(path)
    if not meta:
        return True  # no frontmatter → legacy file, show it
    return meta.get("status") not in ("draft", "template")


def exchange_code_for_token(code: str, client_id: str, client_secret: str, redirect_uri: str):
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    resp = requests.post(url, headers=headers, data=data, timeout=10)
    resp.raise_for_status()
    j = resp.json()
    return j.get("access_token")


def fetch_github_user(token: str):
    url = "https://api.github.com/user"
    headers = {"Authorization": f"token {token}", "Accept": "application/json"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


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


def main():
    is_panel = st.query_params.get("mode", "") == "panel"
    page_title = "Panel Event — Facilitator" if is_panel else "ECBA Study Session — Facilitator"
    st.set_page_config(page_title=page_title, layout="wide")
    st.html(BRAND_CSS)
    st.title(page_title)

    # Ensure facilitator is always defined (guards Notes/Actions/Complete steps)
    facilitator = st.session_state.get("facilitator", "")

    events = load_events()
    if events.empty:
        st.warning("No events found in etn/outputs/iiba_events_parsed.csv — using sample data.")

    titles = events.get("title", events.get("Title", events.columns.tolist())).tolist()
    if not titles:
        titles = ["(no events)"]

    # Attempt to auto-login from persistent session
    persisted = load_persistent_session()
    if persisted and not st.session_state.get("logged_in"):
        try:
            exp = datetime.datetime.fromisoformat(persisted.get("expires"))
            if exp > datetime.datetime.utcnow():
                st.session_state["facilitator"] = persisted.get("name")
                st.session_state["logged_in"] = True
                st.session_state["token"] = persisted.get("token")
                facilitator = st.session_state["facilitator"]
        except Exception:
            pass

    with st.sidebar:
        # GitHub OAuth callback handling
        params = st.query_params
        if "code" in params and not st.session_state.get("logged_in"):
            code = params.get("code")
            client_id = os.environ.get("GITHUB_CLIENT_ID")
            client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
            redirect_uri = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8501/")
            if client_id and client_secret:
                try:
                    token = exchange_code_for_token(code, client_id, client_secret, redirect_uri)
                    if token:
                        user = fetch_github_user(token)
                        if user:
                            st.session_state["facilitator"] = user.get("login")
                            st.session_state["logged_in"] = True
                            st.session_state["token"] = token
                            facilitator = st.session_state["facilitator"]
                            expires = (
                                datetime.datetime.utcnow() + datetime.timedelta(days=7)
                            ).isoformat()
                            save_persistent_session(user.get("login"), token, expires)
                            st.rerun()
                except Exception as e:
                    st.error(f"GitHub OAuth failed: {e}")

        if not st.session_state.get("logged_in"):
            st.markdown("### Sign in")
            gh_client = os.environ.get("GITHUB_CLIENT_ID")
            redirect_uri = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8501/")
            if gh_client:
                state = uuid.uuid4().hex
                oauth_params = {
                    "client_id": gh_client,
                    "redirect_uri": redirect_uri,
                    "scope": "read:user",
                    "state": state,
                }
                url = "https://github.com/login/oauth/authorize?" + urllib.parse.urlencode(
                    oauth_params
                )
                st.markdown(f"[Sign in with GitHub]({url})")
            else:
                pass  # GitHub OAuth not configured; local login available below

            if gh_client:
                st.markdown("---")
                st.markdown("Or use the local login:")
            login_name = st.text_input("Facilitator name")
            login_pass = st.text_input("Password", type="password")
            remember = st.checkbox("Remember me (7 days)")
            if st.button("Log in"):
                expected = os.environ.get("FACILITATOR_PASSWORD", "facilitate")
                if login_pass == expected and login_name:
                    st.session_state["facilitator"] = login_name
                    st.session_state["logged_in"] = True
                    token = uuid.uuid4().hex
                    st.session_state["token"] = token
                    if remember:
                        expires = (
                            datetime.datetime.utcnow() + datetime.timedelta(days=7)
                        ).isoformat()
                        save_persistent_session(login_name, token, expires)
                    st.rerun()
                else:
                    st.error("Invalid name or password")
        else:
            facilitator = st.session_state.get("facilitator", "")
            st.markdown(f"**Logged in as:** {facilitator}")
            if st.button("Log out"):
                st.session_state["logged_in"] = False
                st.session_state["facilitator"] = ""
                st.session_state.pop("token", None)
                clear_persistent_session()
                st.rerun()

        event_choice = st.selectbox("Select event", titles)

        if is_panel:
            STEPS = ["Run of Show", "Panelist Briefing", "Q&A Cues", "Notes", "Actions", "Complete"]
        else:
            STEPS = ["Overview", "Discussion prompts", "Notes", "Actions", "Complete", "Case Study"]
        st.sidebar.markdown("---")
        step = st.sidebar.radio("Step", STEPS, key="radio_step")

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

    # Variant folder path intentionally not shown to avoid leaking internal structure

    master_text = load_master_context(selected_variant)

    preview_path = find_preview_file(selected_variant)
    preview_text = read_preview(preview_path)
    with st.expander("Variant preview (Plan / README)"):
        if preview_path:
            st.markdown(f"**Preview file:** {preview_path.name}")
            st.markdown(preview_text)
        else:
            st.info("No plan or README found to preview in this variant folder.")

    docs = find_documents(selected_variant)

    # Panel mode: supplement with panel event templates
    if is_panel:
        panel_docs = sorted(_PANEL_EVENT_DIR.glob("*.md")) if _PANEL_EVENT_DIR.exists() else []
        docs = panel_docs + [d for d in docs if d not in panel_docs]

    # Published-only filter: hide draft/template files in facilitator view
    show_published_only = st.sidebar.checkbox("Published only", value=True, key="pub_filter")
    if show_published_only:
        docs = [d for d in docs if _is_published(d)]
    params = st.query_params
    open_param = params.get("open")
    presenter_param = params.get("presenter")
    slide_param = params.get("slide")
    open_path = None

    if not open_param and preview_path:
        open_path = preview_path
        open_param = str(preview_path)

    # Panel mode: auto-open moderator script if no file is selected
    if is_panel and not open_param:
        ms = _PANEL_EVENT_DIR / "moderator_script.md"
        if ms.exists():
            open_path = ms
            open_param = str(ms)
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

    with st.expander("Documents (click to open)"):
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
                            if st.button("Prev"):
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
                        st.markdown("**Timer**")
                        tkey = f"timer_{key_idx}_{safe_open}"
                        if tkey not in st.session_state:
                            st.session_state[tkey] = {
                                "running": False,
                                "end": None,
                                "remaining": 0,
                            }

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

    if not is_panel:
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

    # Case study gating UI (ECBA mode only)
    if not is_panel and step == "Case Study":
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

    if not is_panel:
        if step == "Overview":
            st.write("Follow the event summary, goals, and desired outcomes.")
            if st.button("Start discussion"):
                st.rerun()

        if step == "Discussion prompts":
            for prompt in session["prompts"]:
                st.write(f"- {prompt}")

    if is_panel:
        if step == "Run of Show":
            st.markdown("Use the **Moderator Script** (loaded above) as your run-of-show. "
                        "Open the document viewer to follow along.")
            st.info("Tip: open the moderator_script.md document above for the full timed script.")

        if step == "Panelist Briefing":
            st.markdown("### Pre-event panelist checklist")
            items = [
                "Confirm attendance and A/V setup (send day-of reminder)",
                "Share audience description and key themes",
                "Review moderator question bank with panelists",
                "Confirm recording consent",
                "Set expectations: 90-second answer target, moderator may redirect",
            ]
            for item in items:
                st.checkbox(item, key=f"panbrief_{item[:20]}")

        if step == "Q&A Cues":
            st.markdown("### Audience Q&A facilitation cues")
            cues = [
                "**Volume down:** 'Let me bring in someone with a different angle on that…'",
                "**Volume up:** 'Can you say more about that? That's something this audience deals with.'",
                "**Bridge:** 'That connects to what [other panelist] said — do you agree?'",
                "**Wrap a tangent:** 'That's a great thread — let's take that offline. Back to the main question…'",
                "**Time signal:** 'We have time for two more questions…'",
            ]
            for cue in cues:
                st.markdown(f"- {cue}")

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
