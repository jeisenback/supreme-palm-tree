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

# Some Streamlit builds may not expose the experimental query API; provide a safe shim.
if not hasattr(st, "experimental_get_query_params"):
    def _shim_get_query_params():
        return {}
    st.experimental_get_query_params = _shim_get_query_params

# Shim for experimental_rerun for Streamlit builds that don't expose it.
if not hasattr(st, "experimental_rerun"):
    def _shim_experimental_rerun():
        try:
            # Prefer changing query params to force a reload if available
            if hasattr(st, "experimental_set_query_params"):
                st.experimental_set_query_params(_rs=uuid.uuid4().hex)
                return
        except Exception:
            pass
        # Fallback: toggle a session token so UI widgets see a change
        try:
            st.session_state["_rerun_token"] = uuid.uuid4().hex
        except Exception:
            pass
        try:
            st.stop()
        except Exception:
            return

    st.experimental_rerun = _shim_experimental_rerun


CSV_PATH = Path("etn/outputs/iiba_events_parsed.csv")
NOTES_PATH = Path("etn/outputs/facilitator_notes.csv")
SESSION_PATH = Path("etn/outputs/facilitator_session.json")


def find_variants():
    base = Path("etn")
    variants = []
    if base.exists():
        for p in sorted(base.glob("ECBA_CaseStudy*")):
            if p.is_dir() and (p / "TrailBlaze_MasterContext.md").exists():
                variants.append(p)
    return variants


def load_master_context(variant_path: Path | None):
    if not variant_path:
        return ""
    master = variant_path / "TrailBlaze_MasterContext.md"
    if master.exists():
        return master.read_text(encoding="utf-8")
    return ""


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


def find_preview_file(variant_path: Path | None) -> Path | None:
    if not variant_path:
        return None
    candidates = [
        "ECBA_CaseStudy_Plan.md",
        "ECBA_CaseStudy_Plan.txt",
        "README.md",
        "README.MD",
    ]
    for name in candidates:
        p = variant_path / name
        if p.exists():
            return p
    # fallback: any .md or .txt in folder
    for p in variant_path.glob("*.md"):
        return p
    for p in variant_path.glob("*.txt"):
        return p
    return None


def read_preview(path: Path | None, max_lines: int = 40) -> str:
    if not path or not path.exists():
        return "(no preview available)"
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return "(failed to read preview)"
    lines = txt.splitlines()
    preview = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        preview += "\n... (truncated)"
    return preview


def find_documents(variant_path: Path | None):
    if not variant_path:
        return []
    docs = []
    for ext in ("*.md", "*.MD", "*.txt", "*.csv", "*.json"):
        for p in sorted(variant_path.rglob(ext)):
            docs.append(p)
    # also include non-markdown interesting files at top-level
    for p in sorted(variant_path.glob("*")):
        if p.is_file() and p.suffix.lower() in (".pdf", ".xlsx") and p not in docs:
            docs.append(p)
    return docs


def linkify_content(content: str, docs: list[Path], base_param: str = "open") -> str:
    # Build mapping from filename and basename -> encoded path
    mapping = {}
    for p in docs:
        rel = str(p).replace("\\", "/")
        mapping[p.name] = urllib.parse.quote(rel)
        mapping[p.stem] = urllib.parse.quote(rel)

    # First, rewrite existing markdown links that point to local files to use ?open=...
    def _replace_md_link(m):
        text = m.group(1)
        target = m.group(2)
        # normalize target (strip anchors and query)
        target_clean = target.split("#")[0].split("?")[0]
        if target_clean in mapping:
            return f"[{text}](?{base_param}={mapping[target_clean]})"
        # if target is a relative path, try matching the basename
        bn = Path(target_clean).name
        if bn in mapping:
            return f"[{text}](?{base_param}={mapping[bn]})"
        return m.group(0)

    content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _replace_md_link, content)

    # Next, replace plain filename mentions (word-boundary). Longer names first
    for name in sorted(mapping.keys(), key=lambda s: -len(s)):
        # avoid touching markdown link syntax we've already processed
        pattern = rf"(?<!\])\b{re.escape(name)}\b"
        repl = f"[{name}](?{base_param}={mapping[name]})"
        content = re.sub(pattern, repl, content)

    return content


def parse_slides(md_text: str) -> list[dict]:
    # Improved slide parsing: handle headings like 'Slide 1', '## Slide 1', 'Slide 1 — Title',
    # and separators. Extract timing and facilitator notes.
    if not md_text:
        return []

    # Normalize line endings
    md = md_text.replace('\r\n', '\n')

    # Find slide headers using several patterns
    header_re = re.compile(r"(?m)^(?:#{1,3}\s*)?(Slide\s+\d+\b.*|Appendix\b.*)$", re.I)
    indices = [m.start() for m in header_re.finditer(md)]
    parts = []
    if indices:
        for i, idx in enumerate(indices):
            start = idx
            end = indices[i+1] if i+1 < len(indices) else len(md)
            parts.append(md[start:end].strip())
    else:
        # fallback: split on top-level '---' separators
        parts = [s.strip() for s in re.split(r"\n-{3,}\n", md) if s.strip()]

    slides = []
    for p in parts:
        lines = p.splitlines()
        if not lines:
            continue
        title_line = lines[0].strip()
        # If first line is not a slide header, try to find a header inside
        if not re.match(r"(?i)^(?:#{1,3}\s*)?(Slide\s+\d+\b|Appendix)", title_line):
            # take first non-empty as title
            title_line = title_line

        # extract timing if present in square brackets or trailing dash
        timing = None
        mtime = re.search(r"\[(.*?)\]", title_line)
        if not mtime:
            mtime = re.search(r"—\s*(\d+:\d+|\d+\s?min|\d+:\d+\s*—)", title_line)
        if mtime:
            timing = mtime.group(1).strip()

        body = "\n".join(lines[1:]).strip()

        # extract facilitator notes using multiple patterns
        notes = []
        def _note_repl(m):
            notes.append(m.group(1).strip())
            return ""

        # patterns: [FACILITATOR: ...], [FACILITATOR], FACILITATOR: on its own line
        body = re.sub(r"\[FACILITATOR:(.*?)\]", _note_repl, body, flags=re.S | re.I)
        body = re.sub(r"\[FACILITATOR\](:?\s*)(.*?)", lambda m: (notes.append(m.group(2).strip()) or ""), body, flags=re.S | re.I)
        # lines like 'FACILITATOR: text'
        body, _ = re.subn(r"(?m)^FACILITATOR:\s*(.*)$", lambda m: (notes.append(m.group(1).strip()) or ""), body)

        slides.append({
            "title": title_line,
            "body": body.strip(),
            "facilitator_notes": notes,
            "timing": timing,
        })

    return slides


def get_session_reveal(master_text: str, session_label: str) -> str:
    # session_label examples: 'SESSION 1 REVEAL', 'SESSION 2 REVEAL', 'SESSION 3 REVEAL'
    if not master_text:
        return "(no master context found)"
    pattern = re.compile(rf"({re.escape(session_label)}.*?)(?=\n---\n|\nSESSION \d|$)", re.S | re.I)
    m = pattern.search(master_text)
    if m:
        return m.group(1).strip()
    # fallback: return whole file
    return master_text


def render_slide_body(raw_body: str, docs: list[Path], variant_path: Path | None):
    # Render images and videos referenced in markdown, then return cleaned markdown text
    body = raw_body or ""
    # detect image tags ![alt](path)
    img_regex = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    last_end = 0
    segments = []
    for m in img_regex.finditer(body):
        pre = body[last_end:m.start()]
        if pre.strip():
            segments.append(("md", pre))
        alt = m.group(1)
        src = m.group(2).strip()
        # resolve src
        if src.startswith("http://") or src.startswith("https://"):
            segments.append(("img_url", src))
        else:
            # try resolve under variant_path
            if variant_path:
                candidate = (variant_path / src).resolve()
                if candidate.exists():
                    segments.append(("img_file", str(candidate)))
                else:
                    # try basename
                    for p in docs:
                        if p.name == src or p.stem == Path(src).stem:
                            segments.append(("img_file", str(p)))
                            break
                    else:
                        segments.append(("img_url", src))
            else:
                segments.append(("img_url", src))
        last_end = m.end()
    tail = body[last_end:]
    if tail.strip():
        segments.append(("md", tail))

    # now render segments in order
    rendered_text = ""
    for kind, val in segments:
        if kind == "md":
            rendered_text += val
        elif kind == "img_url":
            try:
                st.image(val)
            except Exception:
                st.markdown(f"![image]({val})")
        elif kind == "img_file":
            try:
                st.image(val)
            except Exception:
                st.markdown(f"![image]({val})")

    # detect youtube links and embed
    yt_match = re.search(r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[^\s)]+)", rendered_text)
    if yt_match:
        url = yt_match.group(1)
        try:
            st.video(url)
        except Exception:
            pass
        # remove the raw url from text
        rendered_text = rendered_text.replace(url, "")

    # finally linkify remaining markdown content
    linked = linkify_content(rendered_text, docs)
    return linked


def exchange_code_for_token(code: str, client_id: str, client_secret: str, redirect_uri: str) -> str | None:
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


def fetch_github_user(token: str) -> dict | None:
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
        # sample fallback
        df = pd.DataFrame(
            [
                {
                    "title": "Sample Study Session",
                    "date": "2025-06-10 19:00",
                    "format": "Virtual",
                    "link": "https://example.org/event",
                    "notes": "Sample event for prototype",
                }
            ]
        )
    return df


def get_query_params():
    try:
        return st.experimental_get_query_params()
    except Exception:
        return {}


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
    st.set_page_config(page_title="Facilitator UI (Prototype)", layout="wide")
    st.title("Facilitator session — prototype")

    events = load_events()
    if events.empty:
        st.warning("No events found in etn/outputs/iiba_events_parsed.csv — using sample data.")

    titles = events.get("title", events.get("Title", events.columns.tolist())).tolist()
    if not titles:
        titles = ["(no events)"]

    # attempt to auto-login from persistent session
    persisted = load_persistent_session()
    if persisted and not st.session_state.get("logged_in"):
        try:
            exp = datetime.datetime.fromisoformat(persisted.get("expires"))
            if exp > datetime.datetime.utcnow():
                st.session_state["facilitator"] = persisted.get("name")
                st.session_state["logged_in"] = True
                st.session_state["token"] = persisted.get("token")
        except Exception:
            pass

    with st.sidebar:
        # Login / session UI
        # GitHub OAuth: if redirect callback contains code, handle exchange
        params = get_query_params()
        if "code" in params and not st.session_state.get("logged_in"):
            code = params.get("code")[0]
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
                            # persist for 7 days
                            expires = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
                            save_persistent_session(user.get("login"), token, expires)
                            st.experimental_rerun()
                except Exception as e:
                    st.error(f"GitHub OAuth failed: {e}")

        if not st.session_state.get("logged_in"):
            st.markdown("### Sign in")
            # GitHub OAuth button/link
            gh_client = os.environ.get("GITHUB_CLIENT_ID")
            redirect_uri = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8501/")
            if gh_client:
                state = uuid.uuid4().hex
                params = {
                    "client_id": gh_client,
                    "redirect_uri": redirect_uri,
                    "scope": "read:user",
                    "state": state,
                }
                url = "https://github.com/login/oauth/authorize?" + urllib.parse.urlencode(params)
                st.markdown(f"[Sign in with GitHub]({url})")
            else:
                st.info("Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to enable GitHub OAuth.")

            st.markdown("---")
            st.markdown("Or use the fallback local login:")
            login_name = st.text_input("Facilitator name")
            login_pass = st.text_input("Password", type="password")
            remember = st.checkbox("Remember me (7 days)")
            if st.button("Log in"):
                # validate password against environment variable or fallback
                expected = os.environ.get("FACILITATOR_PASSWORD", "facilitate")
                if login_pass == expected and login_name:
                    st.session_state["facilitator"] = login_name
                    st.session_state["logged_in"] = True
                    token = uuid.uuid4().hex
                    st.session_state["token"] = token
                    if remember:
                        expires = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
                        save_persistent_session(login_name, token, expires)
                    st.experimental_rerun()
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
                st.experimental_rerun()

        event_choice = st.selectbox("Select event", titles)
        STEPS = ["Overview", "Discussion prompts", "Notes", "Actions", "Complete", "Case Study"]
        # quick nav buttons for views
        for s in STEPS:
            if st.button(s, key=f"nav_{s}"):
                st.session_state["radio_step"] = s
                st.experimental_rerun()

        default_index = 0
        if "radio_step" in st.session_state and st.session_state.get("radio_step") in STEPS:
            default_index = STEPS.index(st.session_state.get("radio_step"))
        st.sidebar.markdown("---")
        st.sidebar.radio("Step", STEPS, index=default_index, key="radio_step")
        step = st.session_state.get("radio_step")

    st.header(event_choice)

    # Variant selector: pick among ECBA_CaseStudy variants under `etn/`
    variants = find_variants()
    variant_names = [p.name for p in variants]
    if not variant_names:
        variant_names = ["ECBA_CaseStudy (not found)"]
        selected_variant = None
    else:
        sel = st.sidebar.selectbox("Case study variant", variant_names, index=0)
        selected_variant = variants[variant_names.index(sel)]

    # show selected variant path in sidebar
    st.sidebar.markdown("**Variant folder:**")
    st.sidebar.write(str(selected_variant) if selected_variant is not None else "(none)")

    master_text = load_master_context(selected_variant)

    # show a short preview of the variant's plan or README
    preview_path = find_preview_file(selected_variant)
    preview_text = read_preview(preview_path)
    with st.expander("Variant preview (Plan / README)"):
        if preview_path:
            st.markdown(f"**Preview file:** {preview_path.name}")
            st.text(preview_text)
        else:
            st.info("No plan or README found to preview in this variant folder.")

    # Documents listing and cross-linking
    docs = find_documents(selected_variant)
    params = get_query_params()
    open_param = params.get("open", [None])[0]
    presenter_param = params.get("presenter", [None])[0]
    slide_param = params.get("slide", [None])[0]
    open_path = None
    # If no explicit document requested, default to the variant preview to show useful content
    if not open_param and preview_path:
        open_path = preview_path
        open_param = str(preview_path)
    if open_param:
        # decode path
        try:
            possible = Path(urllib.parse.unquote(open_param))
            # if relative path provided, resolve against repo
            if not possible.is_absolute():
                possible = Path(possible)
            if possible.exists():
                open_path = possible
            else:
                # try resolving under selected_variant
                if selected_variant:
                    candidate = selected_variant.joinpath(urllib.parse.unquote(open_param)).resolve()
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

    # If a document is explicitly requested via ?open=..., render it (with cross-links)
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
        if not is_slide_deck and isinstance(raw, str) and re.search(r"(?m)^Slide\s+\d+\b", raw):
            is_slide_deck = True

        # Slide deck UI
        if is_slide_deck and open_path.suffix.lower() in (".md", ".txt"):
            slides = parse_slides(raw)
            if not slides:
                st.markdown("(no slides parsed)")
            else:
                # compute a filesystem-safe key fragment for this open_path
                safe_open = str(open_path).replace('\\', '_').replace('/', '_')
                key_idx = f"slide_idx_{safe_open}"
                if key_idx not in st.session_state:
                    st.session_state[key_idx] = 0

                # If a slide index is provided via query param, respect it (audience/presenter sync)
                try:
                    if slide_param is not None:
                        sval = int(slide_param)
                        if 0 <= sval < len(slides):
                            st.session_state[key_idx] = sval
                except Exception:
                    pass

                idx = st.session_state[key_idx]

                # If ?presenter=true is set, show a presenter-optimized layout intended for a separate tab/window
                if presenter_param and presenter_param.lower() in ("1", "true", "yes"):
                    st.markdown("**Presenter View — open in a separate window for presenting**")
                    pcol_main, pcol_side = st.columns([8, 3])
                    with pcol_main:
                        s = slides[idx]
                        st.markdown(f"# {s['title']}")
                        rendered = render_slide_body(s['body'], docs, selected_variant)
                        st.markdown(rendered, unsafe_allow_html=False)
                        nav1, nav2, nav3 = st.columns([1, 1, 6])
                        with nav1:
                            if st.button("Prev"):
                                st.session_state[key_idx] = max(0, st.session_state[key_idx] - 1)
                                st.experimental_rerun()
                        with nav2:
                            if st.button("Next"):
                                st.session_state[key_idx] = min(len(slides) - 1, st.session_state[key_idx] + 1)
                                st.experimental_rerun()

                        # progress bar
                        progress = int((idx + 1) / max(1, len(slides)) * 100)
                        st.progress(progress)

                        # Keyboard & auto JS controls: a small HTML snippet that can start/stop a timer
                        # The JS updates the `slide` query param which is read above to sync presenter/audience.
                        open_enc = urllib.parse.quote(str(open_path).replace('\\', '/'))
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
                                                    document.getElementById('stop_btn').addEventListener('click', function(){{ if(timer) clearInterval(timer); }});
                                                    // keyboard navigation
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
                        js = js.replace('__OPEN_ENC__', open_enc)
                        js = js.replace('__IDX__', str(idx)).replace('__MAXIDX__', str(len(slides)-1))
                        components.html(js, height=120)

                    with pcol_side:
                        st.markdown("**Facilitator notes**")
                        s = slides[idx]
                        if s['facilitator_notes']:
                            for n in s['facilitator_notes']:
                                st.write(n)
                        else:
                            st.write("(no notes)")

                        st.markdown("---")
                        st.markdown("**Timer**")
                        tkey = f"timer_{key_idx}_{safe_open}"
                        if tkey not in st.session_state:
                            st.session_state[tkey] = {"running": False, "end": None, "remaining": 0}

                        minutes = st.number_input("Minutes", min_value=0, max_value=180, value=10, step=1, key=f"min_{tkey}")
                        if st.button("Start", key=f"start_{tkey}"):
                            st.session_state[tkey]["running"] = True
                            st.session_state[tkey]["end"] = time.time() + int(minutes) * 60
                            st.session_state[tkey]["remaining"] = int(minutes) * 60
                            st.experimental_rerun()
                        if st.button("Pause", key=f"pause_{tkey}"):
                            if st.session_state[tkey]["running"] and st.session_state[tkey]["end"]:
                                st.session_state[tkey]["remaining"] = max(0, int(st.session_state[tkey]["end"] - time.time()))
                                st.session_state[tkey]["running"] = False
                                st.session_state[tkey]["end"] = None
                        if st.button("Reset", key=f"reset_{tkey}"):
                            st.session_state[tkey] = {"running": False, "end": None, "remaining": int(minutes) * 60}
                            st.experimental_rerun()

                        # display countdown
                        if st.session_state[tkey]["running"] and st.session_state[tkey]["end"]:
                            remaining = int(st.session_state[tkey]["end"] - time.time())
                            if remaining <= 0:
                                st.warning("Time's up")
                                st.session_state[tkey]["running"] = False
                                st.session_state[tkey]["end"] = None
                                st.session_state[tkey]["remaining"] = 0
                            else:
                                mins = remaining // 60
                                secs = remaining % 60
                                st.markdown(f"## {mins:02d}:{secs:02d}")
                                time.sleep(1)
                                st.experimental_rerun()
                        else:
                            rem = st.session_state[tkey].get("remaining", 0)
                            mins = rem // 60
                            secs = rem % 60
                            st.markdown(f"## {mins:02d}:{secs:02d}")

                        st.markdown("---")
                        st.markdown("Open audience view:")
                        aud_rel = urllib.parse.quote(str(open_path).replace('\\', '/'))
                        aud_link = f"?open={aud_rel}"
                        st.markdown(f"[Open audience view]({aud_link})")

                else:
                    col1, col2, col3 = st.columns([1, 6, 2])
                    with col1:
                        if st.button("Previous"):
                            st.session_state[key_idx] = max(0, st.session_state[key_idx] - 1)
                            st.experimental_rerun()
                        if st.button("Next"):
                            st.session_state[key_idx] = min(len(slides) - 1, st.session_state[key_idx] + 1)
                            st.experimental_rerun()
                        st.write(f"{idx+1}/{len(slides)}")
                        st.slider("Jump to", 1, len(slides), idx+1, key=f"slider_{key_idx}", on_change=lambda: st.session_state.update({key_idx: st.session_state[f"slider_{key_idx}"]-1}))

                    with col2:
                        s = slides[idx]
                        st.markdown(f"### {s['title']}")
                        # presenter controls
                        presenter_mode = st.checkbox("Presenter mode", value=st.session_state.get("presenter_mode", False))
                        st.session_state["presenter_mode"] = presenter_mode

                        if presenter_mode:
                            # auto-advance controls
                            auto = st.checkbox("Auto-advance", value=st.session_state.get("auto_advance", False))
                            st.session_state["auto_advance"] = auto
                            interval = st.slider("Interval (seconds)", 2, 60, value=10)
                            st.session_state["auto_interval"] = interval
                            if auto:
                                # sleep then advance (prototype only)
                                time.sleep(interval)
                                st.session_state[key_idx] = min(len(slides) - 1, st.session_state[key_idx] + 1)
                                st.experimental_rerun()

                        body_to_render = s['body']
                        rendered = render_slide_body(body_to_render, docs, selected_variant)
                        st.markdown(rendered, unsafe_allow_html=False)

                    with col3:
                        show_notes = st.checkbox("Show facilitator notes", value=True)
                        if show_notes and s['facilitator_notes']:
                            st.markdown("**Facilitator notes:**")
                            for n in s['facilitator_notes']:
                                st.write(n)

                    # quick links to practice questions referenced in deck
                    pq = [p for p in docs if 'PracticeQuestions' in p.name]
                    if pq:
                        st.markdown("---")
                        st.markdown("**Practice question sets:**")
                        for p in pq:
                            rel = str(p).replace('\\', '/')
                            st.markdown(f"- [{p.name}](?open={urllib.parse.quote(rel)})")

        else:
            # For markdown files, linkify internal references
            if open_path.suffix.lower() in (".md", ".txt"):
                linked = linkify_content(raw, docs)
                st.markdown(linked, unsafe_allow_html=False)
            else:
                # For non-text formats, provide a download link
                st.download_button("Download file", data=open_path.read_bytes(), file_name=open_path.name)

    # Session mapping: month -> session number (for auto-select)
    MONTH_SESSION_MAP = {
        4: 1,  # April -> Session 1
        5: 2,  # May -> Session 2
        6: 3,  # June -> Session 3
        7: 4,  # July -> Session 4
        8: 5,  # August -> Session 5
    }

    SESSIONS = {
        1: {
            "title": "Session 1 — Foundations & Core Concepts",
            "agenda": [
                "ARCS cold open (10 min)",
                "Concepts: BA mindset, BACCM (25 min)",
                "Guided application: BACCM exercise (8 min)",
                "Group exercise: Stakeholder identification + problem statement (25 min)",
                "Practice round: 4 timed MCQs (8 min)",
            ],
            "homework": "Refine problem statement; 6 exam MCQs",
            "prompts": [
                "What went well?",
                "What assumptions did you make?",
                "Trace each requirement to a measurable criterion.",
            ],
            "practice_questions": [
                {
                    "q": "Which BACCM element identifies who benefits from a change?",
                    "choices": ["Change", "Need", "Stakeholder", "Solution"],
                    "a": 2,
                },
                {
                    "q": "A good problem statement should be:",
                    "choices": ["Vague and broad", "Measurable and specific", "Solution-oriented", "Optional"],
                    "a": 1,
                },
            ],
        },
        2: {
            "title": "Session 2 — Planning, Elicitation & Context",
            "agenda": [
                "Homework share-out (10 min)",
                "Concepts: BA planning & elicitation (25 min)",
                "Group exercise: BA approach (20 min)",
            ],
            "homework": "Draft BA approach recommendation; 6 exam MCQs",
            "prompts": ["Which stakeholders to engage first?", "What elicitation techniques suit this stakeholder?"],
            "practice_questions": [
                {
                    "q": "Which elicitation technique is best for detailed requirements?",
                    "choices": ["Survey", "Interview", "Observation", "Brainstorming"],
                    "a": 1,
                }
            ],
        },
        3: {
            "title": "Session 3 — Change, Need & Requirements Lifecycle",
            "agenda": ["Current/future-state framing", "Convert raw needs to requirements", "RTM basics"],
            "homework": "Convert 3 raw needs into requirements; 6 MCQs",
            "prompts": ["How would you verify this requirement?", "Who owns this requirement?"],
            "practice_questions": [
                {
                    "q": "A testable requirement should be:",
                    "choices": ["Ambiguous", "Measurable", "Open-ended", "Opinion-based"],
                    "a": 1,
                }
            ],
        },
        4: {
            "title": "Session 4 — Solution, Stakeholder & Requirements Analysis",
            "agenda": ["RADD concepts", "Solution options analysis", "RTM linking"],
            "homework": "Write recommendation with 3 traced requirements; 6 MCQs",
            "prompts": ["Which option best traces to the RTM?", "What are the NFR risks?"],
            "practice_questions": [
                {
                    "q": "Which is an NFR?",
                    "choices": ["Booking flow", "Performance < 500ms", "Checkout label", "Hero image"],
                    "a": 1,
                }
            ],
        },
        5: {
            "title": "Session 5 — Value, Review & Exam Readiness",
            "agenda": ["Pilot results reveal", "Post-pilot KPI analysis", "Exam simulation"],
            "homework": "KPI analysis; integrated exam practice",
            "prompts": ["Which requirements failed to trace to outcomes?", "What sequencing errors occurred?"],
            "practice_questions": [
                {
                    "q": "Pilot target was 100 bookings; actual was 87. This is a: ",
                    "choices": ["Success", "Missed target (13%)", "Irrelevant", "Partial fulfillment"],
                    "a": 1,
                }
            ],
        },
    }

    # Auto-select session based on current month, allow manual override
    now = datetime.datetime.now()
    default_session = MONTH_SESSION_MAP.get(now.month)
    session_selected = st.sidebar.selectbox("Session (auto-selected by month)",
                                           ["Auto-select"] + [f"Session {i}" for i in range(1, 6)],
                                           index=0)
    if session_selected == "Auto-select":
        session_num = default_session or 1
    else:
        session_num = int(session_selected.split()[1])

    session = SESSIONS.get(session_num)

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
        st.markdown("**Warning:** This document contains session-gated reveals. Do not distribute to participants.")
        confirm = st.checkbox("I confirm I am the facilitator and will not share reveals with participants")
        session_select = st.selectbox("Select session reveal to view", [
            "Full document",
            "SESSION 1 REVEAL",
            "SESSION 2 REVEAL",
            "SESSION 3 REVEAL",
            "SESSION 4 REVEAL",
            "SESSION 5 REVEAL",
        ])
        if confirm:
            if session_select == "Full document":
                st.markdown("---")
                st.text(master_text)
            else:
                reveal = get_session_reveal(master_text, session_select)
                st.markdown("---")
                st.text(reveal)
        else:
            st.info("Check the confirmation box to reveal gated content.")

    # show event details if available
    if event_choice != "(no events)":
        row = events[events.get("title", events.get("Title", "title")) == event_choice]
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
            st.experimental_rerun()

    if step == "Discussion prompts":
        st.write("- What went well?\n- What could be improved?\n- Actions and owners.")

    if step == "Notes":
        key = f"note_{event_choice}_{step}"
        note = st.text_area("Notes", value=st.session_state.get(key, ""), height=200)
        st.session_state[key] = note
        if st.button("Save note"):
            save_note(event_choice, facilitator, step, note)
            st.success("Saved")

    if step == "Actions":
        action = st.text_input("Action item")
        owner = st.text_input("Owner")
        due = st.date_input("Due date")
        if st.button("Save action"):
            save_note(event_choice, facilitator, step, f"Action: {action}; Owner: {owner}; Due: {due}")
            st.success("Action saved")

    if step == "Complete":
        completed = st.checkbox("Mark session complete")
        if st.button("Finalize"):
            save_note(event_choice, facilitator, step, "Finalized", completed=completed)
            st.success("Session finalized")

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"Notes saved: {NOTES_PATH.name if NOTES_PATH.exists() else 'none'}")


if __name__ == "__main__":
    main()
