"""
Content Studio — IIBA East Tennessee Chapter
Gap Radar · Editor · AI Draft
"""

import re
import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))

from brand import BRAND_CSS
from content_types import CONTENT_TYPES, STYLE_RULES
from frontmatter_utils import read_frontmatter, write_frontmatter, scan_content_library

try:
    sys.path.insert(0, str(_PROJECT_ROOT / "agents"))
    from llm_adapter import generate_content_draft, APIKeyError, ContentGenerationError
    _LLM_AVAILABLE = True
except ImportError:
    _LLM_AVAILABLE = False

_ECBA_DIR = _PROJECT_ROOT / "etn" / "ECBA_CaseStudy"
_TEMPLATES_DIR = _PROJECT_ROOT / "etn" / "templates"

_STATUS_BADGE = {
    "published": '<span class="gap-radar-published">● published</span>',
    "draft":     '<span class="gap-radar-draft">● draft</span>',
    "missing":   '<span class="gap-radar-gap">○ missing</span>',
    "template":  '<span style="color:#888">◌ template</span>',
}


# ---------------------------------------------------------------------------
# Library loader (cached per session, reloaded on demand)
# ---------------------------------------------------------------------------

def _load_library() -> list[dict]:
    entries = []
    for d in [_ECBA_DIR, _TEMPLATES_DIR]:
        entries.extend(scan_content_library(d))
    return entries


def _reload():
    st.session_state["library"] = _load_library()
    st.session_state["library_ts"] = True


def _library() -> list[dict]:
    if "library" not in st.session_state:
        _reload()
    return st.session_state["library"]


# ---------------------------------------------------------------------------
# Style checker
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
                warnings.append(f"Non-standard cue(s) found — use [FACILITATOR: ...] format")
    return warnings


# ---------------------------------------------------------------------------
# Gap Radar tab
# ---------------------------------------------------------------------------

def _radar_table(entries: list[dict], content_type: str, rows: list, row_label: str,
                 slots: list[str], required_slots: list[str]) -> str:
    """Build an HTML table for one content type's gap grid."""

    def get_status(row_key, slot) -> str:
        for e in entries:
            if e["content_type"] != content_type:
                continue
            row_match = (
                e.get("session_id") == row_key
                if content_type == "ecba_session"
                else e.get("subtype") == row_key
            )
            if row_match and e.get("slot") == slot:
                return e.get("status", "draft")
        return "missing"

    req_set = set(required_slots)
    header_cells = "".join(
        f'<th>{"★ " if s in req_set else ""}{s.replace("_"," ")}</th>'
        for s in slots
    )
    header = f"<tr><th>{row_label}</th>{header_cells}</tr>"

    body_rows = []
    for row_key in rows:
        label = f"Session {row_key}" if content_type == "ecba_session" else row_key.replace("_", " ").title()
        cells = "".join(
            f'<td>{_STATUS_BADGE[get_status(row_key, s)]}</td>'
            for s in slots
        )
        body_rows.append(f"<tr><td><strong>{label}</strong></td>{cells}</tr>")

    return f"""
    <style>
      .gap-table {{ border-collapse: collapse; width: 100%; font-size: 0.88rem; }}
      .gap-table th, .gap-table td {{
        border: 1px solid #C6D0D0;
        padding: 0.45rem 0.75rem;
        text-align: left;
      }}
      .gap-table th {{ background: #F5F5F5; font-family: 'Roboto Condensed', sans-serif; }}
      .gap-table tr:hover td {{ background: #FAFAFA; }}
    </style>
    <table class="gap-table"><thead>{header}</thead><tbody>{"".join(body_rows)}</tbody></table>
    """


def _gap_radar_tab(library: list[dict]) -> None:
    col_refresh, col_legend = st.columns([5, 1])
    with col_legend:
        if st.button("↻ Refresh", use_container_width=True):
            _reload()
            st.rerun()

    # Summary counts
    total = len(library)
    published = sum(1 for e in library if e["status"] == "published")
    draft = sum(1 for e in library if e["status"] == "draft")
    missing_ecba = sum(
        1
        for s in range(1, 6)
        for slot in CONTENT_TYPES["ecba_session"]["required"]
        if not any(
            e["content_type"] == "ecba_session"
            and e.get("session_id") == s
            and e.get("slot") == slot
            for e in library
        )
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total files", total)
    m2.metric("Published", published)
    m3.metric("Drafts", draft)
    m4.metric("Required gaps", missing_ecba, delta=f"-{missing_ecba}" if missing_ecba else None,
              delta_color="inverse")

    st.divider()

    # ECBA sessions grid
    st.subheader("ECBA Study Sessions")
    ecba_slots = CONTENT_TYPES["ecba_session"]["slots"]
    ecba_required = CONTENT_TYPES["ecba_session"]["required"]
    st.html(_radar_table(library, "ecba_session", list(range(1, 6)), "Session",
                         ecba_slots, ecba_required))
    st.caption("★ = required slot")

    st.divider()

    # Career Accelerator grid (required slots only for clarity)
    st.subheader("Career Accelerator")
    ca_subtypes = CONTENT_TYPES["career_accelerator"]["subtypes"]
    ca_required = CONTENT_TYPES["career_accelerator"]["required"]
    st.html(_radar_table(library, "career_accelerator", ca_subtypes, "Subtype",
                         ca_required, ca_required))

    st.divider()

    # Panel event grid
    st.subheader("Panel Events")
    pe_slots = CONTENT_TYPES["panel_event"]["slots"]
    pe_required = CONTENT_TYPES["panel_event"]["required"]
    # Panel events don't have a fixed subtype list — show template row
    pe_rows = list({e.get("subtype") or "—" for e in library if e["content_type"] == "panel_event"}) or ["(template)"]
    st.html(_radar_table(library, "panel_event", pe_rows, "Event",
                         pe_slots, pe_required))


# ---------------------------------------------------------------------------
# Editor tab
# ---------------------------------------------------------------------------

def _editor_tab(library: list[dict]) -> None:
    if not library:
        st.info("No managed content files found. Add YAML frontmatter to content in etn/ to start.")
        return

    # Build display labels for selectbox
    def _label(e: dict) -> str:
        ct = e.get("content_type", "?")
        sid = e.get("session_id")
        slot = (e.get("slot") or "?").replace("_", " ")
        status = e.get("status", "draft")
        subtype = e.get("subtype") or ""
        if ct == "ecba_session":
            prefix = f"Session {sid}" if sid else ct
        elif ct == "career_accelerator":
            prefix = subtype.replace("_", " ").title() if subtype else ct
        else:
            prefix = ct.replace("_", " ").title()
        badge = {"published": "✅", "draft": "🟡", "template": "📋"}.get(status, "⬜")
        return f"{badge}  {prefix} / {slot}"

    options = library
    labels = [_label(e) for e in options]

    col_sel, col_meta = st.columns([2, 1])
    with col_sel:
        idx = st.selectbox("Select file", range(len(labels)), format_func=lambda i: labels[i])

    entry = options[idx]
    path = entry["path"]

    with col_meta:
        st.markdown("**Metadata**")
        st.caption(f"`{path.relative_to(_PROJECT_ROOT)}`")
        st.caption(
            f"type: `{entry['content_type']}` &nbsp;·&nbsp; "
            f"slot: `{entry['slot']}` &nbsp;·&nbsp; "
            f"status: `{entry['status']}`"
        )

    metadata, body = read_frontmatter(path)

    # Style warnings (computed from saved content, not the editor buffer)
    warnings = _check_style(body, entry.get("slot", ""))
    if warnings:
        with st.expander(f"⚠️ {len(warnings)} style warning(s)", expanded=False):
            for w in warnings:
                st.warning(w, icon="⚠️")

    # Editor form
    with st.form("editor_form", border=False):
        new_body = st.text_area(
            "Content",
            value=body,
            height=480,
            label_visibility="collapsed",
        )

        col_save, col_publish, col_preview = st.columns([1, 1, 2])
        save_clicked = col_save.form_submit_button("💾 Save draft", use_container_width=True)
        publish_clicked = col_publish.form_submit_button("🚀 Publish", use_container_width=True,
                                                          type="primary")

    if save_clicked or publish_clicked:
        new_meta = dict(metadata)
        if publish_clicked:
            new_meta["status"] = "published"
        else:
            new_meta.setdefault("status", "draft")
        try:
            write_frontmatter(path, new_meta, new_body)
            _reload()
            action = "Published" if publish_clicked else "Saved"
            st.success(f"{action}: `{path.name}`")
            # Re-check style on new content
            fresh_warnings = _check_style(new_body, entry.get("slot", ""))
            if fresh_warnings:
                for w in fresh_warnings:
                    st.warning(w, icon="⚠️")
        except (ValueError, OSError) as exc:
            st.error(f"Write failed: {exc}")

    # Preview toggle
    with st.expander("Preview", expanded=False):
        st.markdown(body, unsafe_allow_html=False)


# ---------------------------------------------------------------------------
# AI Draft tab
# ---------------------------------------------------------------------------

def _ai_draft_tab(library: list[dict]) -> None:
    if not _LLM_AVAILABLE:
        st.warning("LLM adapter could not be imported. Check `agents/llm_adapter.py`.")
        return

    st.markdown("Generate a content draft using AI. The draft is saved as a **new file** in `etn/` — "
                "it won't overwrite existing content.")

    col_type, col_slot = st.columns(2)
    with col_type:
        ct = st.selectbox("Content type", list(CONTENT_TYPES.keys()),
                          format_func=lambda x: x.replace("_", " ").title())
    with col_slot:
        slots = CONTENT_TYPES[ct]["slots"]
        slot = st.selectbox("Slot", slots, format_func=lambda x: x.replace("_", " ").title())

    # Subtype picker (career_accelerator only)
    subtype = ""
    if ct == "career_accelerator":
        subtype = st.selectbox(
            "Subtype",
            CONTENT_TYPES["career_accelerator"]["subtypes"],
            format_func=lambda x: x.replace("_", " ").title(),
        )

    # Session ID
    if ct == "ecba_session":
        session_id = st.number_input("Session number", min_value=1, max_value=5, value=1, step=1)
    elif ct == "career_accelerator":
        from content_types import SUBTYPE_IDS
        session_id = SUBTYPE_IDS.get(subtype, 100)
    else:
        session_id = None

    # Grounding context
    with st.expander("Grounding context (optional)", expanded=False):
        st.caption("Paste existing content, speaker notes, or a session outline to guide generation.")
        context_text = st.text_area("Context", height=180, label_visibility="collapsed",
                                     placeholder="Paste context here…")

    context = {"raw": context_text} if context_text.strip() else {}

    # Generate
    if st.button("✨ Generate draft", type="primary"):
        with st.spinner("Generating…"):
            try:
                draft = generate_content_draft(ct, slot, context)
                st.session_state["ai_draft"] = draft
                st.session_state["ai_draft_meta"] = {
                    "content_type": ct,
                    "slot": slot,
                    "subtype": subtype,
                    "session_id": session_id,
                    "status": "draft",
                }
            except APIKeyError:
                st.error("ANTHROPIC_API_KEY is not set. Add it to your environment.")
                return
            except ContentGenerationError as exc:
                st.error(f"Generation failed: {exc}")
                return

    draft = st.session_state.get("ai_draft", "")
    if not draft:
        return

    st.divider()
    st.subheader("Generated draft")

    edited_draft = st.text_area("Edit before saving", value=draft, height=400,
                                 label_visibility="collapsed")

    # Save path
    if ct == "ecba_session":
        default_filename = f"Session{session_id}_{slot}.md"
        default_dir = _ECBA_DIR
    elif ct == "career_accelerator":
        default_filename = f"{subtype}_{slot}.md"
        default_dir = _TEMPLATES_DIR / "career_accelerator"
    else:
        default_filename = f"panel_{slot}.md"
        default_dir = _TEMPLATES_DIR / "panel_event"

    col_path, col_save = st.columns([3, 1])
    with col_path:
        filename = st.text_input("Save as", value=default_filename)
    with col_save:
        st.write("")  # vertical alignment
        save_draft = st.button("💾 Save draft", use_container_width=True)

    if save_draft:
        save_path = default_dir / filename
        meta = dict(st.session_state.get("ai_draft_meta", {}))
        try:
            write_frontmatter(save_path, meta, edited_draft)
            _reload()
            st.success(f"Saved: `{save_path.relative_to(_PROJECT_ROOT)}`")
            st.session_state.pop("ai_draft", None)
        except (ValueError, OSError) as exc:
            st.error(f"Save failed: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Content Studio — IIBA ETN",
        page_icon="📝",
        layout="wide",
    )
    st.html(BRAND_CSS)
    st.html('<div class="hero-section"><p class="hero-eyebrow">IIBA East Tennessee Chapter</p>'
            '<h1 class="hero-title">Content Studio</h1>'
            '<p class="hero-subtitle">Gap Radar · Editor · AI Draft</p></div>')

    library = _library()

    tab_radar, tab_editor, tab_draft = st.tabs(["📊 Gap Radar", "✏️ Editor", "✨ AI Draft"])

    with tab_radar:
        _gap_radar_tab(library)

    with tab_editor:
        _editor_tab(library)

    with tab_draft:
        _ai_draft_tab(library)


if __name__ == "__main__":
    main()
