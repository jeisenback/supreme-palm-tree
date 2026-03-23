"""
ECBA Study Program — Board Showcase
A clean, no-login presentation of the ECBA certification study program
for IIBA East TN board members and prospective participants.
"""

import urllib.parse
from pathlib import Path

import streamlit as st

from shared import (
    SESSIONS,
    MONTH_SESSION_MAP,
    find_variants,
    load_master_context,
    find_documents,
    find_slide_deck,
    parse_slides,
    linkify_content,
)

# ── Brand CSS ─────────────────────────────────────────────────────────────────

BRAND_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@700&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  /* Global typography */
  html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    color: #002E38;
  }
  h1, h2, h3, h4, h5, h6 {
    font-family: 'Roboto Condensed', system-ui, sans-serif;
    font-weight: 700;
  }

  /* Hero section */
  .hero-section {
    background-color: #DB5D00;
    padding: 3.5rem 2rem 2.5rem;
    text-align: center;
    border-radius: 4px;
    margin-bottom: 2rem;
  }
  .hero-eyebrow {
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 600;
    color: rgba(255,255,255,0.9);
    font-size: 0.95rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
  }
  .hero-title {
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: #FFFFFF;
    font-size: 2.75rem;
    line-height: 1.15;
    margin: 0 0 0.75rem;
  }
  .hero-tagline {
    font-family: 'IBM Plex Sans', sans-serif;
    color: rgba(255,255,255,0.95);
    font-size: 1.15rem;
    line-height: 1.6;
    max-width: 600px;
    margin: 0 auto 1.25rem;
  }
  .hero-meta {
    font-family: 'IBM Plex Sans', sans-serif;
    color: rgba(255,255,255,0.85);
    font-size: 0.9rem;
    letter-spacing: 0.05em;
  }

  /* Section headers */
  .section-header {
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: #002E38;
    font-size: 1.85rem;
    padding-bottom: 0.4rem;
    border-bottom: 4px solid #DB5D00;
    margin-bottom: 1.5rem;
  }

  /* Session timeline node */
  .session-node {
    text-align: center;
    padding: 0.75rem 0.5rem;
  }
  .session-dot {
    width: 48px;
    height: 48px;
    background-color: #DB5D00;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 0.5rem;
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: white;
    font-size: 1.1rem;
  }
  .session-month {
    font-family: 'IBM Plex Sans', sans-serif;
    color: #00758C;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .session-title-small {
    font-family: 'IBM Plex Sans', sans-serif;
    color: #002E38;
    font-size: 0.8rem;
    margin-top: 0.25rem;
    line-height: 1.3;
  }

  /* Slide cards */
  .slide-card {
    background: #FFFFFF;
    border: 1px solid #C6D0D0;
    border-top: 4px solid #DB5D00;
    border-radius: 4px;
    padding: 1.25rem 1rem;
    min-height: 200px;
  }
  .slide-card .session-label {
    font-family: 'IBM Plex Sans', sans-serif;
    color: #00758C;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
  }
  .slide-card h3 {
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: #002E38;
    font-size: 1rem;
    margin: 0 0 0.5rem;
  }
  .slide-card p {
    font-family: 'IBM Plex Sans', sans-serif;
    color: #002E38;
    font-size: 0.875rem;
    line-height: 1.55;
    margin: 0;
  }
  .slide-empty {
    color: #888;
    font-style: italic;
    font-size: 0.875rem;
  }

  /* TrailBlaze section */
  .trailblaze-section {
    background-color: #DB5D00;
    border-radius: 4px;
    padding: 2.5rem 2rem;
    margin: 1rem 0;
  }
  .trailblaze-section h2 {
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: #FFFFFF;
    font-size: 2rem;
    margin-bottom: 1rem;
  }
  .trailblaze-section p {
    font-family: 'IBM Plex Sans', sans-serif;
    color: rgba(255,255,255,0.97);
    font-size: 1.05rem;
    line-height: 1.75;
    margin: 0;
  }
  .trailblaze-stat {
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: #FFFFFF;
    font-size: 1.4rem;
    border-top: 2px solid rgba(255,255,255,0.4);
    padding-top: 1rem;
    margin-top: 1rem;
    text-align: center;
  }

  /* MCQ section */
  .mcq-container {
    background: #F5F5F5;
    border-radius: 4px;
    padding: 1.5rem;
    margin-bottom: 1rem;
  }
  .mcq-question {
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 600;
    color: #002E38;
    font-size: 1.05rem;
    margin-bottom: 1rem;
  }

  /* Section divider */
  .section-divider {
    border: none;
    border-top: 1px solid #C6D0D0;
    margin: 2.5rem 0;
  }
</style>
"""

# ── Session months for timeline display ──────────────────────────────────────
SESSION_MONTHS = {1: "April", 2: "May", 3: "June", 4: "July", 5: "August"}


# ── App ───────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="ECBA Study Program — IIBA East TN",
        page_icon="🎓",
        layout="wide",
    )

    # Inject brand CSS + Google Fonts
    st.markdown(BRAND_CSS, unsafe_allow_html=True)

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

    # ── Section 2: Curriculum Timeline ───────────────────────────────────────
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

    # ── Section 3: Sample Slides ──────────────────────────────────────────────
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

    # ── Section 4: Interactive Practice MCQ ──────────────────────────────────
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

    # ── Section 5: TrailBlaze Case Study ──────────────────────────────────────
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

    # ── Section 6: Document Browser ──────────────────────────────────────────
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
