"""Shared utilities for ECBA study program Streamlit apps."""

import re
import urllib.parse
import warnings
from pathlib import Path

import yaml
import streamlit as st


# ── Month → Session mapping ───────────────────────────────────────────────────

MONTH_SESSION_MAP = {
    4: 1,  # April
    5: 2,  # May
    6: 3,  # June
    7: 4,  # July
    8: 5,  # August
}


# ── Session content — loaded from etn/ECBA_CaseStudy/sessions/session_N.yaml ─

_SESSIONS_DIR = Path(__file__).parent.parent / "etn" / "ECBA_CaseStudy" / "sessions"


def _load_sessions() -> dict:
    """Load all session_N.yaml files and return {session_id: session_dict}.

    Falls back gracefully: missing or malformed files produce a warning and
    an empty entry so callers never receive a KeyError on valid session IDs.
    """
    sessions = {}
    for n in range(1, 6):
        yaml_path = _SESSIONS_DIR / f"session_{n}.yaml"
        if not yaml_path.exists():
            warnings.warn(f"Session YAML not found: {yaml_path}", stacklevel=2)
            sessions[n] = {}
            continue
        try:
            with open(yaml_path, encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            sessions[n] = data or {}
        except Exception as exc:
            warnings.warn(f"Failed to load {yaml_path}: {exc}", stacklevel=2)
            sessions[n] = {}
    return sessions


SESSIONS: dict = _load_sessions()


# ── Cached I/O functions ──────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def find_variants() -> list:
    base = Path("etn")
    variants = []
    if base.exists():
        for p in sorted(base.glob("ECBA_CaseStudy*")):
            if p.is_dir() and (p / "TrailBlaze_MasterContext.md").exists():
                variants.append(p)
    return variants


@st.cache_data(ttl=60)
def load_master_context(variant_path) -> str:
    if not variant_path:
        return ""
    master = Path(variant_path) / "TrailBlaze_MasterContext.md"
    if master.exists():
        return master.read_text(encoding="utf-8")
    return ""


@st.cache_data(ttl=60)
def find_preview_file(variant_path):
    if not variant_path:
        return None
    vp = Path(variant_path)
    candidates = [
        "ECBA_CaseStudy_Plan.md",
        "ECBA_CaseStudy_Plan.txt",
        "README.md",
        "README.MD",
    ]
    for name in candidates:
        p = vp / name
        if p.exists():
            return p
    for p in vp.glob("*.md"):
        return p
    for p in vp.glob("*.txt"):
        return p
    return None


@st.cache_data(ttl=60)
def read_preview(path, max_lines: int = 40) -> str:
    if not path:
        return "(no preview available)"
    p = Path(path)
    if not p.exists():
        return "(no preview available)"
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        return "(failed to read preview)"
    lines = txt.splitlines()
    preview = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        preview += "\n... (truncated)"
    return preview


@st.cache_data(ttl=60)
def find_documents(variant_path) -> list:
    if not variant_path:
        return []
    vp = Path(variant_path)
    docs = []
    for ext in ("*.md", "*.MD", "*.txt", "*.csv", "*.json"):
        for p in sorted(vp.rglob(ext)):
            docs.append(p)
    for p in sorted(vp.glob("*")):
        if p.is_file() and p.suffix.lower() in (".pdf", ".xlsx") and p not in docs:
            docs.append(p)
    return docs


@st.cache_data(ttl=60)
def find_slide_deck(variant_path):
    """Return the first slide deck (.md/.txt with slide content) in variant_path."""
    if not variant_path:
        return None
    vp = Path(variant_path)
    for p in sorted(vp.glob("*")):
        if p.is_file() and p.suffix.lower() in (".md", ".txt"):
            if "slide" in p.name.lower() or "slides" in p.name.lower():
                return p
    # fallback: any .md containing "Slide N" headers
    for p in sorted(vp.glob("*.md")):
        try:
            txt = p.read_text(encoding="utf-8")
            if re.search(r"(?m)^Slide\s+\d+\b", txt):
                return p
        except Exception:
            pass
    return None


# ── Pure utility functions ────────────────────────────────────────────────────

def linkify_content(content: str, docs: list, base_param: str = "open") -> str:
    mapping = {}
    for p in docs:
        p = Path(p)
        rel = str(p).replace("\\", "/")
        mapping[p.name] = urllib.parse.quote(rel)
        mapping[p.stem] = urllib.parse.quote(rel)

    def _replace_md_link(m):
        text = m.group(1)
        target = m.group(2)
        target_clean = target.split("#")[0].split("?")[0]
        if target_clean in mapping:
            return f"[{text}](?{base_param}={mapping[target_clean]})"
        bn = Path(target_clean).name
        if bn in mapping:
            return f"[{text}](?{base_param}={mapping[bn]})"
        return m.group(0)

    content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _replace_md_link, content)

    for name in sorted(mapping.keys(), key=lambda s: -len(s)):
        pattern = rf"(?<!\])\b{re.escape(name)}\b"
        repl = f"[{name}](?{base_param}={mapping[name]})"
        content = re.sub(pattern, repl, content)

    return content


def parse_slides(md_text: str) -> list:
    if not md_text:
        return []

    md = md_text.replace('\r\n', '\n')

    header_re = re.compile(r"(?m)^(?:#{1,3}\s*)?(Slide\s+\d+\b.*|Appendix\b.*)$", re.I)
    indices = [m.start() for m in header_re.finditer(md)]
    parts = []
    if indices:
        for i, idx in enumerate(indices):
            start = idx
            end = indices[i + 1] if i + 1 < len(indices) else len(md)
            parts.append(md[start:end].strip())
    else:
        parts = [s.strip() for s in re.split(r"\n-{3,}\n", md) if s.strip()]

    slides = []
    for p in parts:
        lines = p.splitlines()
        if not lines:
            continue
        title_line = lines[0].strip()

        timing = None
        mtime = re.search(r"\[(.*?)\]", title_line)
        if not mtime:
            mtime = re.search(r"—\s*(\d+:\d+|\d+\s?min|\d+:\d+\s*—)", title_line)
        if mtime:
            timing = mtime.group(1).strip()

        body = "\n".join(lines[1:]).strip()

        notes = []

        def _note_repl(m):
            notes.append(m.group(1).strip())
            return ""

        body = re.sub(r"\[FACILITATOR:(.*?)\]", _note_repl, body, flags=re.S | re.I)
        body = re.sub(
            r"\[FACILITATOR\](:?\s*)(.*?)",
            lambda m: (notes.append(m.group(2).strip()) or ""),
            body,
            flags=re.S | re.I,
        )
        body, _ = re.subn(
            r"(?m)^FACILITATOR:\s*(.*)$",
            lambda m: (notes.append(m.group(1).strip()) or ""),
            body,
        )

        slides.append({
            "title": title_line,
            "body": body.strip(),
            "facilitator_notes": notes,
            "timing": timing,
        })

    return slides


def get_session_reveal(master_text: str, session_label: str) -> str:
    if not master_text:
        return "(no master context found)"
    pattern = re.compile(
        rf"({re.escape(session_label)}.*?)(?=\n---\n|\nSESSION \d|$)", re.S | re.I
    )
    m = pattern.search(master_text)
    if m:
        return m.group(1).strip()
    return master_text


def render_slide_body(raw_body: str, docs: list, variant_path) -> str:
    body = raw_body or ""
    vp = Path(variant_path) if variant_path else None
    img_regex = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    last_end = 0
    segments = []
    for m in img_regex.finditer(body):
        pre = body[last_end:m.start()]
        if pre.strip():
            segments.append(("md", pre))
        src = m.group(2).strip()
        if src.startswith("http://") or src.startswith("https://"):
            segments.append(("img_url", src))
        else:
            if vp:
                candidate = (vp / src).resolve()
                if candidate.exists():
                    segments.append(("img_file", str(candidate)))
                else:
                    for p in docs:
                        p = Path(p)
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

    rendered_text = ""
    for kind, val in segments:
        if kind == "md":
            rendered_text += val
        elif kind in ("img_url", "img_file"):
            try:
                st.image(val)
            except Exception:
                st.markdown(f"![image]({val})")

    yt_match = re.search(
        r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[^\s)]+)",
        rendered_text,
    )
    if yt_match:
        url = yt_match.group(1)
        try:
            st.video(url)
        except Exception:
            pass
        rendered_text = rendered_text.replace(url, "")

    return linkify_content(rendered_text, docs)
