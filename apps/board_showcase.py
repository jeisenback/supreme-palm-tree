"""
ECBA Study Program — Board Showcase
A clean, no-login presentation of the ECBA certification study program
for IIBA East TN board members and prospective participants.
"""

import urllib.parse
from pathlib import Path

import streamlit as st

from brand import BRAND_CSS

try:
    from learner_tracking import get_board_metrics, _DEFAULT_DB as _LEARNER_DB
    _LEARNER_AVAILABLE = True
except ImportError:
    _LEARNER_AVAILABLE = False
from shared import (
    SESSIONS,
    find_variants,
    load_master_context,
    find_documents,
    find_slide_deck,
    parse_slides,
    linkify_content,
)

# ── Session months for timeline display ──────────────────────────────────────
SESSION_MONTHS = {1: "April", 2: "May", 3: "June", 4: "July", 5: "August"}


# ── Outcomes helper ───────────────────────────────────────────────────────────

def _outcomes_section():
    """Show aggregate learner metrics. Silent no-op if db doesn't exist yet."""
    if not _LEARNER_AVAILABLE:
        return
    db = _LEARNER_DB
    if not Path(db).exists():
        return

    try:
        m = get_board_metrics(db)
    except Exception:
        return

    if m["total_members"] == 0:
        return

    st.markdown('<div class="section-header">Program Outcomes</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Members enrolled", m["total_members"])
    col2.metric("Attendance rate", f"{m['avg_attendance_rate']:.0%}")
    col3.metric("Homework rate", f"{m['homework_completion_rate']:.0%}")
    col4.metric("Avg readiness", f"{m['avg_readiness_score']}/100")
    st.caption("Source: attendance records — updated after each session")


# ── App ───────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="ECBA Study Program — IIBA East TN",
        page_icon="🎓",
        layout="wide",
    )

    # Inject brand CSS + Google Fonts (st.html avoids rendering CSS text as visible content)
    st.html(BRAND_CSS)

    # ── Detect variant (optional — app works without it) ─────────────────────
    variants = find_variants()
    selected_variant = variants[0] if variants else None

    # ── Section 1: Hero ───────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-section">
          <div class="hero-eyebrow">IIBA East Tennessee Chapter</div>
          <h1 class="hero-title">ECBA Certification Study Program</h1>
          <p class="hero-tagline">
            Preparing East Tennessee business professionals for ECBA certification —
            one study group at a time.
          </p>
          <div class="hero-meta">5 sessions &nbsp;·&nbsp; April – August &nbsp;·&nbsp; Virtual &nbsp;·&nbsp; Prepare for ECBA</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Section 2: Program Outcomes (learner metrics) ────────────────────────
    _outcomes_section()

    # ── Section 3: Curriculum Timeline ───────────────────────────────────────
    st.markdown('<div class="section-header">The Program</div>', unsafe_allow_html=True)

    cols = st.columns(5)
    for i, col in enumerate(cols, start=1):
        session = SESSIONS[i]
        month = SESSION_MONTHS[i]
        with col:
            st.markdown(
                f"""
                <div class="session-node">
                  <div class="session-dot">S{i}</div>
                  <div class="session-month">{month}</div>
                  <div class="session-title-small">{session['title'].split('—',1)[-1].strip()}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander(f"Session {i} details"):
                st.markdown(f"**{session['title']}**")
                st.markdown("**Agenda:**")
                for item in session["agenda"]:
                    st.write(f"- {item}")
                st.markdown(f"**Homework:** {session['homework']}")
                st.markdown("**Discussion prompts:**")
                for prompt in session["prompts"]:
                    st.write(f"- {prompt}")

    # ── Section 4: Sample Slides ──────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">A Glimpse Inside</div>', unsafe_allow_html=True
    )
    st.markdown(
        '<p style="color:#002E38;margin-bottom:1rem">Real slides from the curriculum — '
        "this is what participants see in session.</p>",
        unsafe_allow_html=True,
    )

    slide_deck_path = find_slide_deck(selected_variant) if selected_variant else None
    slides = []
    if slide_deck_path:
        try:
            raw = slide_deck_path.read_text(encoding="utf-8")
            slides = parse_slides(raw)
        except Exception:
            slides = []

    slide_cols = st.columns(3)
    placeholder_msg = (
        "Slide decks are loaded from your local variant folder. "
        "Ask your facilitator for access."
    )
    for col_idx, col in enumerate(slide_cols):
        with col:
            if col_idx < len(slides):
                s = slides[col_idx]
                # Strip facilitator notes — board members don't see those
                body_preview = s["body"][:300].strip()
                if len(s["body"]) > 300:
                    body_preview += "…"
                st.markdown(
                    f"""
                    <div class="slide-card">
                      <div class="session-label">Curriculum slide</div>
                      <h3>{s['title']}</h3>
                      <p>{body_preview if body_preview else '&nbsp;'}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="slide-card">
                      <div class="session-label">Curriculum slide</div>
                      <p class="slide-empty">{placeholder_msg}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── Section 5: Interactive Practice MCQ ──────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">Try It Yourself</div>', unsafe_allow_html=True
    )
    st.markdown(
        '<p style="color:#002E38;margin-bottom:1rem">This is where <strong>you</strong> '
        "practice what a real BA does. Try a sample question from the program.</p>",
        unsafe_allow_html=True,
    )

    sample_q = SESSIONS[1]["practice_questions"][0]

    st.markdown(
        f'<div class="mcq-question">{sample_q["q"]}</div>',
        unsafe_allow_html=True,
    )
    choice = st.radio(
        "Select your answer:",
        sample_q["choices"],
        key="board_mcq_choice",
        label_visibility="collapsed",
    )
    if st.button("Check Answer", key="board_mcq_check", type="primary"):
        correct_answer = sample_q["choices"][sample_q["a"]]
        if choice == correct_answer:
            st.success(
                f"Correct! **{correct_answer}** — Stakeholders are the people who "
                "benefit from or are affected by a change. That's BACCM in action."
            )
        else:
            st.error(
                f"Not quite. The correct answer is **{correct_answer}**. "
                "In the BACCM framework, Stakeholders are those who benefit from "
                "or are impacted by a change."
            )

    # ── Section 6: TrailBlaze Case Study ──────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    tb_col, stat_col = st.columns([3, 2])
    with tb_col:
        st.markdown(
            """
            <div class="trailblaze-section">
              <h2>The TrailBlaze Case Study</h2>
              <p>
                Meet TrailBlaze — a tech startup expanding into a new city. Participants
                step into the role of a business analyst: they interview stakeholders, analyze
                needs, define requirements, and recommend a solution. The twist? Every session
                reveals a new development. By Session 5, you've worked a complete BA engagement
                — start to finish.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with stat_col:
        st.markdown(
            """
            <div class="trailblaze-section" style="height:100%">
              <div class="trailblaze-stat">5 sessions</div>
              <div class="trailblaze-stat">1 continuous story</div>
              <div class="trailblaze-stat">Real BA skills</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Section 7: Document Browser ──────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">Explore All Materials</div>',
        unsafe_allow_html=True,
    )

    if not selected_variant:
        st.info("Connect your variant folder to explore materials.")
    else:
        docs = find_documents(selected_variant)
        if not docs:
            st.info(
                "No documents found — check that the variant folder contains .md, "
                ".txt, or .csv files."
            )
        else:
            # Variant picker (if multiple variants)
            if len(variants) > 1:
                variant_names = [v.name for v in variants]
                sel_name = st.selectbox(
                    "Variant", variant_names, index=0, key="board_variant_sel"
                )
                sel_variant = variants[variant_names.index(sel_name)]
                docs = find_documents(sel_variant)
            else:
                sel_variant = selected_variant

            # File list
            st.markdown("**Available materials:**")
            doc_cols = st.columns(2)
            for i, p in enumerate(docs):
                rel = str(p).replace("\\", "/")
                link = f"?open={urllib.parse.quote(rel)}"
                doc_cols[i % 2].markdown(f"- [{p.name}]({link})")

            # Inline viewer for ?open= param
            open_param = st.query_params.get("open")
            if open_param:
                open_path = None
                try:
                    possible = Path(urllib.parse.unquote(open_param))
                    if possible.exists():
                        open_path = possible
                    elif sel_variant:
                        candidate = sel_variant.joinpath(
                            urllib.parse.unquote(open_param)
                        ).resolve()
                        if candidate.exists():
                            open_path = candidate
                except Exception:
                    pass

                if open_path and open_path.exists():
                    st.markdown("---")
                    st.subheader(f"Viewing: {open_path.name}")
                    if open_path.suffix.lower() in (".md", ".txt"):
                        try:
                            raw = open_path.read_text(encoding="utf-8")
                        except Exception:
                            raw = "(could not read file)"
                        linked = linkify_content(raw, docs)
                        st.markdown(linked, unsafe_allow_html=False)
                    elif open_path.suffix.lower() in (".csv",):
                        try:
                            import pandas as pd
                            df = pd.read_csv(open_path)
                            st.dataframe(df)
                        except Exception as e:
                            st.error(f"Could not read file: {e}")
                    else:
                        st.download_button(
                            "Download file",
                            data=open_path.read_bytes(),
                            file_name=open_path.name,
                        )
                else:
                    st.warning("Document not found. Check that the path is correct.")


if __name__ == "__main__":
    main()
