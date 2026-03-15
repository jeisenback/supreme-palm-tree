"""Folder watcher: triggers ingestion when files are added to a watch directory.

This PoC uses `watchdog` if available; otherwise falls back to a simple polling
implementation. The watcher exposes `start_watcher(path, callback)` which will
call `callback(file_path)` for new files.
"""
from __future__ import annotations

import os
import time
import threading
from typing import Callable
import threading
from typing import Optional

def start_drive_watcher(
    folder_id: str,
    callback: Callable[[str], None],
    poll_interval: float = 30.0,
    background: bool = True,
    credentials_json: Optional[str] = None,
    credential_type: str = "service_account",
    oauth_token_path: Optional[str] = None,
):
    """Poll a Google Drive folder for new files and call `callback(local_path)`.

    This is a simple polling implementation that remembers seen file ids in
    memory for the lifetime of the process. It downloads new files to a
    temporary directory and invokes `callback` with the local path.
    """
    try:
        from integrations.gdrive.drive_client import DriveClient
    except Exception:
        raise RuntimeError("Drive integration not available in this environment")

    import tempfile

    seen = set()

    def _loop():
        client = DriveClient(credentials_json=credentials_json, folder_id=folder_id, credential_type=credential_type, oauth_token_path=oauth_token_path)
        tmpdir = tempfile.mkdtemp(prefix="drivewatch-")
        while True:
            try:
                files = client.list_files(folder_id=folder_id)
            except Exception:
                files = []
            for f in files:
                fid = f.get("id")
                name = f.get("name")
                if fid in seen:
                    continue
                seen.add(fid)
                # download file
                local = None
                try:
                    local = Path(tmpdir) / name
                    client.download_file(fid, str(local))
                    callback(str(local))
                except Exception:
                    # ignore individual download failures
                    continue
            time.sleep(poll_interval)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return thread


def _polling_watcher(path: str, callback: Callable[[str], None], poll_interval: float = 2.0):
    seen = set()
    while True:
        try:
            entries = [os.path.join(path, f) for f in os.listdir(path)]
        except Exception:
            entries = []
        for p in entries:
            if p not in seen and os.path.isfile(p):
                seen.add(p)
                try:
                    callback(p)
                except Exception:
                    pass
        time.sleep(poll_interval)


def start_watcher(path: str, callback: Callable[[str], None], background: bool = True) -> threading.Thread | None:
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Watch path not found: {path}")

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class _Handler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    try:
                        callback(event.src_path)
                    except Exception:
                        pass

        observer = Observer()
        handler = _Handler()
        observer.schedule(handler, path, recursive=False)
        observer.start()

        if background:
            return observer  # type: ignore
        else:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                observer.join()
                return None
    except Exception:
        # fallback to polling watcher
        thread = threading.Thread(target=_polling_watcher, args=(path, callback), daemon=True)
        thread.start()
        return thread
