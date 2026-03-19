from __future__ import annotations

import os
from typing import Optional
import json
import os


class DriveClient:
    """Google Drive client that can upload files using a service account.

    This implementation uses `google-auth` and `google-api-python-client`.
    It intentionally guards against missing dependencies and missing
    credentials so the rest of the codebase can import this module safely.
    """

    def __init__(
        self,
        credentials_json: Optional[str] = None,
        folder_id: Optional[str] = None,
        credential_type: str = "service_account",
        oauth_token_path: Optional[str] = None,
    ) -> None:
        """Construct DriveClient.

        - `credential_type` controls how credentials are interpreted: "service_account" or "oauth".
        - When using OAuth, `credentials_json` should point to the client secrets file and
          `oauth_token_path` may be provided to persist tokens.
        """
        self.credentials_json = credentials_json
        self.folder_id = folder_id
        self.credential_type = credential_type
        self.oauth_token_path = oauth_token_path

    def upload_file(self, path: str, mime_type: Optional[str] = None) -> dict:
        """Upload `path` to Google Drive and return the file metadata.

        Expects `credentials_json` to be a path to a service account JSON file.
        Raises `RuntimeError` with a clear message if dependencies or
        credentials are missing.
        """
        # Lazy import of google libraries; provide clear error messages when missing.
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
        except Exception as e:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "Missing Google Drive dependencies. Install `google-api-python-client` and `google-auth` to enable Drive uploads"
            ) from e

        creds = None
        if self.credential_type == "service_account":
            try:
                from google.oauth2 import service_account

                if not self.credentials_json or not os.path.exists(self.credentials_json):
                    raise RuntimeError("Google Drive service account credentials file not found or not configured")

                creds = service_account.Credentials.from_service_account_file(
                    self.credentials_json, scopes=["https://www.googleapis.com/auth/drive.file"]
                )
            except Exception as e:  # pragma: no cover - environment dependent
                raise RuntimeError("Failed to load service account credentials") from e

        elif self.credential_type == "oauth":
            try:
                # Load token if present
                token = None
                if self.oauth_token_path and os.path.exists(self.oauth_token_path):
                    try:
                        with open(self.oauth_token_path, "r", encoding="utf-8") as fh:
                            token_data = json.load(fh)
                            token = token_data.get("token")
                    except Exception:
                        token = None

                # Attempt to import google-auth classes
                from google.oauth2.credentials import Credentials as OAuthCredentials

                if token:
                    creds = OAuthCredentials(token)
                else:
                    # No token available; instruct caller to run OAuth flow helper
                    raise RuntimeError("OAuth token not found; run the OAuth flow to obtain credentials")
            except Exception as e:
                raise RuntimeError("Failed to load OAuth credentials") from e

        else:
            raise RuntimeError(f"Unsupported credential_type: {self.credential_type}")

        service = build("drive", "v3", credentials=creds, cache_discovery=False)

        file_metadata = {"name": os.path.basename(path)}
        if self.folder_id:
            file_metadata["parents"] = [self.folder_id]

        media = MediaFileUpload(path, mimetype=mime_type)
        created = service.files().create(body=file_metadata, media_body=media, fields="id,name,mimeType,parents").execute()
        return created

    def list_files(self, folder_id: Optional[str] = None) -> list[dict]:
        """List files in a folder. Returns list of dicts with id,name,mimeType,modifiedTime.

        This is a lightweight wrapper around Drive API list; raises RuntimeError
        if dependencies or credentials are missing (same as `upload_file`).
        """
        try:
            from googleapiclient.discovery import build
        except Exception as e:  # pragma: no cover - environment dependent
            raise RuntimeError("Missing Google Drive dependencies. Install google-api-python-client and google-auth") from e

        # reuse auth loading from upload_file path
        # Simple approach: attempt to construct credentials similarly
        creds = None
        if self.credential_type == "service_account":
            try:
                from google.oauth2 import service_account

                if not self.credentials_json or not os.path.exists(self.credentials_json):
                    raise RuntimeError("Google Drive service account credentials file not found or not configured")

                creds = service_account.Credentials.from_service_account_file(
                    self.credentials_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
                )
            except Exception as e:
                raise RuntimeError("Failed to load service account credentials") from e
        elif self.credential_type == "oauth":
            try:
                token = None
                if self.oauth_token_path and os.path.exists(self.oauth_token_path):
                    try:
                        with open(self.oauth_token_path, "r", encoding="utf-8") as fh:
                            import json as _json

                            token_data = _json.load(fh)
                            token = token_data.get("token")
                    except Exception:
                        token = None
                from google.oauth2.credentials import Credentials as OAuthCredentials

                if token:
                    creds = OAuthCredentials(token)
                else:
                    raise RuntimeError("OAuth token not found; run the OAuth flow to obtain credentials")
            except Exception as e:
                raise RuntimeError("Failed to load OAuth credentials") from e

        service = build("drive", "v3", credentials=creds, cache_discovery=False)

        q = None
        if folder_id:
            q = f"'{folder_id}' in parents and trashed = false"

        resp = service.files().list(q=q, fields="files(id,name,mimeType,modifiedTime)").execute()
        return resp.get("files", [])

    def download_file(self, file_id: str, dest_path: str) -> None:
        """Download a Drive file by id to `dest_path`.

        Uses MediaIoBaseDownload; raises RuntimeError if dependencies missing.
        """
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseDownload
        except Exception as e:  # pragma: no cover - environment dependent
            raise RuntimeError("Missing Google Drive dependencies. Install google-api-python-client and google-auth") from e

        # load creds same as list_files
        creds = None
        if self.credential_type == "service_account":
            from google.oauth2 import service_account

            creds = service_account.Credentials.from_service_account_file(
                self.credentials_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )
        else:
            from google.oauth2.credentials import Credentials as OAuthCredentials

            token = None
            if self.oauth_token_path and os.path.exists(self.oauth_token_path):
                import json as _json

                try:
                    with open(self.oauth_token_path, "r", encoding="utf-8") as fh:
                        token_data = _json.load(fh)
                        token = token_data.get("token")
                except Exception:
                    token = None
            if not token:
                raise RuntimeError("OAuth token not found; run the OAuth flow to obtain credentials")
            creds = OAuthCredentials(token)

        service = build("drive", "v3", credentials=creds, cache_discovery=False)
        request = service.files().get_media(fileId=file_id)
        import io

        fh = io.FileIO(dest_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.close()
