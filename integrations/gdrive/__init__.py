"""Google Drive integration stubs.

This package contains PoC helpers to integrate exported files to Google Drive.
Actual uploads require user-provided OAuth credentials and are left as a
human step. The `DriveClient` class is a minimal scaffold.
"""

from .drive_client import DriveClient

__all__ = ["DriveClient"]
