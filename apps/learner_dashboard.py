"""
apps/learner_dashboard.py

Cross-session learner tracking dashboard for IIBA ETN.

Three tabs:
  📊 Cohort Overview — chapter-level metrics for board reporting
  👤 Individual Progress — per-member detail with readiness score
  🔥 Attendance Heatmap — member × session grid

Run with:
    streamlit run apps/learner_dashboard.py
"""

import sys
from pathlib import Path

import streamlit as st

_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))

from brand import BRAND_CSS
from learner_tracking import (
    _DEFAULT_DB,
    get_board_metrics,
    get_learner_summary,
    ingest_directory,
    init_db,
    readiness_score,
)

import sqlite3

_ATTENDANCE_DIR = _PROJECT_ROOT / "data" / "attendance"
_DB_PATH = _DEFAULT_DB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_color(score: int) -> str:
    if score >= 75:
        return "#22863a"   # green
    if score >= 40:
        return "#DB5D00"   # brand orange
    return "#b31d28"       # red


def _score_bar(score: int) -> str:
    color = _score_color(score)
    return (
        f'<div style="background:#e0e0e0;border-radius:4px;height:8px;width:120px;display:inline-block">'
        f'<div style="background:{color};width:{score}%;height:8px;border-radius:4px"></div>'
        f'</div> <span style="font-size:0.85em;color:{color};font-weight:600">{score}/100</span>'
    )


def _reload():
    st.session_state.pop("metrics", None)
    st.session_state.pop("summary", None)
    st.rerun()


def _load_data():
    if "metrics" not in st.session_state:
        st.session_state["metrics"] = get_board_metrics(_DB_PATH)
        st.session_state["summary"] = get_learner_summary(_DB_PATH)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

def _cohort_tab(metrics: dict):
    st.subheader("Chapter-Level Metrics")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Members", metrics["total_members"])
    col2.metric("Sessions Logged", metrics["total_sessions_logged"])
    col3.metric("Attendance Rate", f"{metrics['avg_attendance_rate']:.0%}")
    col4.metric("Homework Rate", f"{metrics['homework_completion_rate']:.0%}")

    st.divider()

    col5, col6 = st.columns(2)
    col5.metric("Avg Readiness Score", f"{metrics['avg_readiness_score']}/100")
    col6.metric("Top Readiness Score", f"{metrics['top_readiness_score']}/100")

    if metrics["total_members"] == 0:
        st.info("No attendance data yet. Use the **Ingest CSV** button in the sidebar to load data.")
        return

    st.caption("Source: `data/attendance/` CSVs → `data/learner_records.db`")


def _individual_tab(summary: list[dict]):
    if not summary:
        st.info("No learner data. Ingest attendance CSVs first.")
        return

    st.subheader("Learner Progress")
    search = st.text_input("Search by name or email", placeholder="e.g. alex or @example.com")

    filtered = summary
    if search.strip():
        q = search.strip().lower()
        filtered = [r for r in summary if q in r["name"].lower() or q in r["email"].lower()]

    if not filtered:
        st.warning(f"No members match '{search}'.")
        return

    # Build HTML table
    rows_html = ""
    for r in filtered:
        bar = _score_bar(r["readiness_score"])
        hw_rate = (
            f"{r['ecba_homework']}/{r['ecba_sessions_attended']}"
            if r["ecba_sessions_attended"] > 0 else "—"
        )
        rows_html += (
            f"<tr>"
            f"<td>{r['name']}</td>"
            f"<td style='color:#555;font-size:0.85em'>{r['email']}</td>"
            f"<td style='text-align:center'>{r['ecba_sessions_attended']}/5</td>"
            f"<td style='text-align:center'>{hw_rate}</td>"
            f"<td>{bar}</td>"
            f"</tr>"
        )

    st.html(
        "<table style='width:100%;border-collapse:collapse;font-size:0.9em'>"
        "<thead><tr style='border-bottom:2px solid #002E38;color:#002E38'>"
        "<th style='text-align:left;padding:6px'>Name</th>"
        "<th style='text-align:left;padding:6px'>Email</th>"
        "<th style='padding:6px'>ECBA Sessions</th>"
        "<th style='padding:6px'>Homework</th>"
        "<th style='padding:6px'>Readiness</th>"
        "</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table>"
    )
    st.caption(f"Showing {len(filtered)} of {len(summary)} members")


def _heatmap_tab(db_path: Path):
    st.subheader("Attendance Heatmap")

    conn = init_db(db_path)
    try:
        # Get all distinct sessions
        sessions = conn.execute(
            "SELECT DISTINCT session_date, session_id, session_type "
            "FROM attendance ORDER BY session_date, session_id"
        ).fetchall()

        members = conn.execute(
            "SELECT email, name FROM members ORDER BY name"
        ).fetchall()

        if not sessions or not members:
            st.info("No attendance data yet.")
            return

        # Build lookup: (email, session_date, session_id) → (attended, homework)
        rows = conn.execute(
            "SELECT member_email, session_date, session_id, attended, homework_submitted "
            "FROM attendance"
        ).fetchall()
    finally:
        conn.close()

    lookup = {
        (r["member_email"], r["session_date"], r["session_id"]): r
        for r in rows
    }

    # Header row
    session_labels = []
    for s in sessions:
        sid = f"S{s['session_id']}" if s["session_id"] else s["session_type"][:3].upper()
        session_labels.append(f"{sid}<br><small>{s['session_date']}</small>")

    header = (
        "<table style='border-collapse:collapse;font-size:0.85em'>"
        "<thead><tr>"
        "<th style='text-align:left;padding:4px 8px;color:#002E38'>Member</th>"
        + "".join(
            f"<th style='padding:4px 8px;text-align:center;color:#002E38'>{lbl}</th>"
            for lbl in session_labels
        )
        + "</tr></thead><tbody>"
    )

    body = ""
    for m in members:
        cells = f"<td style='padding:4px 8px;white-space:nowrap'>{m['name']}</td>"
        for s in sessions:
            key = (m["email"], s["session_date"], s["session_id"])
            rec = lookup.get(key)
            if rec is None:
                cell = "·"
                color = "#ccc"
            elif rec["attended"]:
                hw = rec["homework_submitted"]
                cell = "✓✎" if hw else "✓"
                color = "#22863a" if hw else "#00758C"
            else:
                cell = "✗"
                color = "#b31d28"
            cells += f"<td style='text-align:center;padding:4px 8px;color:{color};font-weight:600'>{cell}</td>"
        body += f"<tr>{cells}</tr>"

    st.html(header + body + "</tbody></table>")
    st.caption("✓ = attended  ✓✎ = attended + homework  ✗ = absent  · = no record")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Learner Dashboard — IIBA ETN",
        layout="wide",
        page_icon="📚",
    )
    st.html(BRAND_CSS)
    st.html(
        '<div class="hero-section">'
        '<p class="hero-eyebrow">IIBA East Tennessee Chapter</p>'
        '<h1 class="hero-title">Learner Dashboard</h1>'
        '<p class="hero-subtitle">Attendance · Progress · Readiness</p>'
        "</div>"
    )

    # Sidebar — ingest + refresh
    with st.sidebar:
        st.header("Data")
        if st.button("↻ Refresh", use_container_width=True):
            _reload()

        st.divider()
        st.subheader("Ingest CSVs")
        if st.button("Ingest attendance/", use_container_width=True):
            with st.spinner("Ingesting…"):
                results = ingest_directory(_ATTENDANCE_DIR, _DB_PATH)
            if results:
                for r in results:
                    status = "✓" if not r["errors"] else "✗"
                    st.write(f"{status} {r['file']} — {r['rows_processed']} rows")
            else:
                st.warning("No CSV files found.")
            _reload()

        st.divider()
        st.caption(f"DB: `{_DB_PATH.relative_to(_PROJECT_ROOT)}`")
        st.caption(f"CSV dir: `{_ATTENDANCE_DIR.relative_to(_PROJECT_ROOT)}`")

    _load_data()
    metrics = st.session_state["metrics"]
    summary = st.session_state["summary"]

    tab_cohort, tab_individual, tab_heatmap = st.tabs([
        "📊 Cohort Overview",
        "👤 Individual Progress",
        "🔥 Attendance Heatmap",
    ])

    with tab_cohort:
        _cohort_tab(metrics)

    with tab_individual:
        _individual_tab(summary)

    with tab_heatmap:
        _heatmap_tab(_DB_PATH)


if __name__ == "__main__":
    main()
