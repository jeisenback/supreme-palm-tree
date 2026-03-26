"""Shared utilities for ECBA study program Streamlit apps."""

import re
import urllib.parse
from pathlib import Path

import streamlit as st


# ── Month → Session mapping ───────────────────────────────────────────────────

MONTH_SESSION_MAP = {
    4: 1,  # April
    5: 2,  # May
    6: 3,  # June
    7: 4,  # July
    8: 5,  # August
}


# ── Session content ───────────────────────────────────────────────────────────

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
        "prompts": [
            "Which stakeholders to engage first?",
            "What elicitation techniques suit this stakeholder?",
        ],
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
        "agenda": [
            "Current/future-state framing",
            "Convert raw needs to requirements",
            "RTM basics",
        ],
        "homework": "Convert 3 raw needs into requirements; 6 MCQs",
        "prompts": [
            "How would you verify this requirement?",
            "Who owns this requirement?",
        ],
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
        "agenda": [
            "RADD concepts",
            "Solution options analysis",
            "RTM linking",
        ],
        "homework": "Write recommendation with 3 traced requirements; 6 MCQs",
        "prompts": [
            "Which option best traces to the RTM?",
            "What are the NFR risks?",
        ],
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
        "agenda": [
            "Pilot results reveal",
            "Post-pilot KPI analysis",
            "Exam simulation",
        ],
        "homework": "KPI analysis; integrated exam practice",
        "prompts": [
            "Which requirements failed to trace to outcomes?",
            "What sequencing errors occurred?",
        ],
        "practice_questions": [
            {
                "q": "Pilot target was 100 bookings; actual was 87. This is a:",
                "choices": ["Success", "Missed target (13%)", "Irrelevant", "Partial fulfillment"],
                "a": 1,
            }
        ],
    },
}


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
