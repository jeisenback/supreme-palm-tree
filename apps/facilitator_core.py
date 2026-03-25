"""Auth persistence helpers and shared sidebar rendering for facilitator pages.

Kept intentionally thin — only items that need to be shared across multiple
Streamlit pages without disturbing the existing test surface in facilitator_ui.py.
"""
import datetime
import os
import uuid
import json
import urllib.parse

import requests
import streamlit as st

SESSION_PATH_CORE = __import__("pathlib").Path("etn/outputs/facilitator_session.json")


# ── Session persistence ────────────────────────────────────────────────────────

def save_persistent_session(name: str, token: str, expires_iso: str):
    SESSION_PATH_CORE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"name": name, "token": token, "expires": expires_iso}
    SESSION_PATH_CORE.write_text(json.dumps(payload), encoding="utf-8")


def load_persistent_session():
    if not SESSION_PATH_CORE.exists():
        return None
    try:
        return json.loads(SESSION_PATH_CORE.read_text(encoding="utf-8"))
    except Exception:
        return None


def clear_persistent_session():
    try:
        if SESSION_PATH_CORE.exists():
            SESSION_PATH_CORE.unlink()
    except Exception:
        pass


# ── GitHub OAuth ───────────────────────────────────────────────────────────────

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
    return resp.json().get("access_token")


def fetch_github_user(token: str):
    url = "https://api.github.com/user"
    headers = {"Authorization": f"token {token}", "Accept": "application/json"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ── Auth sidebar ───────────────────────────────────────────────────────────────

def render_auth_sidebar() -> str:
    """Render login/logout UI in the current sidebar context.

    Handles auto-login from persistent session, GitHub OAuth callback, and
    local password login. Returns the facilitator name if logged in, else ''.
    Call this from inside a ``with st.sidebar:`` block.
    """
    params = st.query_params

    # Auto-login from persistent session
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

    # GitHub OAuth callback
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
            st.info(
                "Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to enable GitHub OAuth."
            )
        st.markdown("---")
        st.markdown("Or sign in with a local account:")
        login_name = st.text_input("Facilitator name", key="auth_login_name")
        login_pass = st.text_input("Password", type="password", key="auth_login_pass")
        remember = st.checkbox("Remember me (7 days)", key="auth_remember")
        if st.button("Log in", key="auth_login_btn"):
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
        return ""
    else:
        facilitator = st.session_state.get("facilitator", "")
        st.markdown(f"**Logged in as:** {facilitator}")
        if st.button("Log out", key="auth_logout_btn"):
            st.session_state["logged_in"] = False
            st.session_state["facilitator"] = ""
            st.session_state.pop("token", None)
            clear_persistent_session()
            st.rerun()
        return facilitator
