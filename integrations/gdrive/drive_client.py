from __future__ import annotations

from typing import Optional


class DriveClient:
    """Minimal Google Drive client scaffold (PoC).

    This client does not perform network calls. It documents the expected
    initialization parameters and provides stub methods to be implemented
    once credentials are available.
    """

    def __init__(self, credentials_json: Optional[str] = None, folder_id: Optional[str] = None) -> None:
        self.credentials_json = credentials_json
        self.folder_id = folder_id

    def upload_file(self, path: str, mime_type: Optional[str] = None) -> dict:
        """Stub for uploading a file to Drive.

        Returns a dict with basic metadata on success. Raises RuntimeError
        if credentials are not provided.
        """
        if not self.credentials_json:
            raise RuntimeError("Google Drive credentials not configured")
        # Placeholder: real implementation would use googleapiclient or similar
        return {"id": "stub-file-id", "path": path, "mime_type": mime_type}
