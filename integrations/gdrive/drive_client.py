from __future__ import annotations

import os
from typing import Optional


class DriveClient:
    """Google Drive client that can upload files using a service account.

    This implementation uses `google-auth` and `google-api-python-client`.
    It intentionally guards against missing dependencies and missing
    credentials so the rest of the codebase can import this module safely.
    """

    def __init__(self, credentials_json: Optional[str] = None, folder_id: Optional[str] = None) -> None:
        self.credentials_json = credentials_json
        self.folder_id = folder_id

    def upload_file(self, path: str, mime_type: Optional[str] = None) -> dict:
        """Upload `path` to Google Drive and return the file metadata.

        Expects `credentials_json` to be a path to a service account JSON file.
        Raises `RuntimeError` with a clear message if dependencies or
        credentials are missing.
        """
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
        except Exception as e:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "Missing Google Drive dependencies. Install `google-api-python-client` and `google-auth` to enable Drive uploads"
            ) from e

        if not self.credentials_json or not os.path.exists(self.credentials_json):
            raise RuntimeError("Google Drive credentials file not found or not configured")

        creds = service_account.Credentials.from_service_account_file(
            self.credentials_json, scopes=["https://www.googleapis.com/auth/drive.file"]
        )

        service = build("drive", "v3", credentials=creds, cache_discovery=False)

        file_metadata = {"name": os.path.basename(path)}
        if self.folder_id:
            file_metadata["parents"] = [self.folder_id]

        media = MediaFileUpload(path, mimetype=mime_type)
        created = service.files().create(body=file_metadata, media_body=media, fields="id,name,mimeType,parents").execute()
        return created
