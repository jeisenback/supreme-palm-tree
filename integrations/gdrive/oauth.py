from __future__ import annotations

import os
from typing import Optional


def run_local_oauth_flow(client_secrets_file: str, token_path: Optional[str] = None, scopes: Optional[list[str]] = None):
    """Run a local OAuth flow using `google_auth_oauthlib` and save token.

    Returns credentials object. The function guards against missing
    dependencies and raises `RuntimeError` with actionable text if not
    available.
    """
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import google.auth
    except Exception as e:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Missing OAuth dependencies. Install `google-auth-oauthlib` and `google-auth` to enable OAuth flow"
        ) from e

    scopes = scopes or ["https://www.googleapis.com/auth/drive.file"]
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes=scopes)
    creds = flow.run_local_server(port=0)

    # Optionally persist token
    if token_path:
        try:
            import json

            with open(token_path, "w", encoding="utf-8") as fh:
                # `creds` may be a Credentials object with `to_json` method
                if hasattr(creds, "to_json"):
                    fh.write(creds.to_json())
                else:
                    # Best-effort serialization
                    json.dump({"token": getattr(creds, "token", None)}, fh)
        except Exception:
            # Non-fatal: proceed without persisting
            pass

    return creds
