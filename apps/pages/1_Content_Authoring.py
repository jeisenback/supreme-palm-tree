"""Content Authoring page — author and manage session slide decks and content.

Accessible via the Streamlit multi-page nav when running apps/facilitator_ui.py.
Requires facilitator login; redirects to a gate message if not authenticated.
"""
import datetime

import streamlit as st

from facilitator_core import render_auth_sidebar
from facilitator_ui import (
    _render_content_authoring,
    load_sessions_override,
    read_live_session,
)
from shared import (
    MONTH_SESSION_MAP,
    find_variants,
)

st.set_page_config(
    page_title="Content Authoring — ECBA Facilitator",
    layout="wide",
)

st.title("Content Authoring")

with st.sidebar:
    facilitator = render_auth_sidebar()
    facilitator = st.session_state.get("facilitator", "")
    st.markdown("---")
    # Mirror session status so facilitator always knows current state
    _live = read_live_session()
    if _live and not _live.get("ended_at"):
        st.success("Session Live")
    elif _live and _live.get("ended_at"):
        st.warning("Session Ended")
    else:
        st.caption("Session not started")

if not st.session_state.get("logged_in"):
    st.info("Please sign in (sidebar) to access content authoring.")
    st.stop()

# ── Variant selector ──────────────────────────────────────────────────────────
variants = find_variants()
variant_names = [p.name for p in variants]
if not variant_names:
    st.warning("No case study variants found in the workspace.")
    selected_variant = None
else:
    sel = st.selectbox("Case study variant", variant_names, index=0)
    selected_variant = variants[variant_names.index(sel)]

# ── Session selector ──────────────────────────────────────────────────────────
now = datetime.datetime.now()
default_session = MONTH_SESSION_MAP.get(now.month) or 1
session_selected = st.selectbox(
    "Session (auto-selected by month)",
    ["Auto-select"] + [f"Session {i}" for i in range(1, 6)],
    index=0,
)
if session_selected == "Auto-select":
    session_num = default_session
else:
    session_num = int(session_selected.split()[1])

st.markdown("---")
_render_content_authoring(session_num, selected_variant)
