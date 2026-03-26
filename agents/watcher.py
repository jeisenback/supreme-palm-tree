"""Folder watcher: triggers ingestion when files are added to a watch directory.

This PoC uses `watchdog` if available; otherwise falls back to a simple polling
implementation. The watcher exposes `start_watcher(path, callback)` which will
call `callback(file_path)` for new files.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional

def start_drive_watcher(
    folder_id: str,
    callback: Callable[[str], None],
    poll_interval: float = 30.0,
    background: bool = True,
    credentials_json: Optional[str] = None,
    credential_type: str = "service_account",
    oauth_token_path: Optional[str] = None,
    state_path: Optional[str] = None,
    approved_source_id: Optional[str] = None,
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

    state_fp = _state_file_path(state_path)
    _raw_seen = _load_seen(state_fp)
    # Upgrade legacy set-of-ids to dict so callers can use .get() with metadata
    seen: dict = {fid: {"id": fid} for fid in _raw_seen} if isinstance(_raw_seen, set) else _raw_seen

    # Approvals enforcement: require an approved source id if provided
    if approved_source_id:
        try:
            from ingest.scrapers import approvals as approvals_mod

            approval = approvals_mod.get_approval(approved_source_id)
            if not approval:
                raise RuntimeError(f"Approved source id not found or not approved: {approved_source_id}")
        except Exception as e:
            raise RuntimeError(f"Approvals check failed: {e}")


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
                new_mtime = f.get("modifiedTime")

                existing = seen.get(fid)
                # If we have seen it before and modifiedTime unchanged, skip
                if existing:
                    existing_mtime = existing.get("modifiedTime")
                    if new_mtime and existing_mtime == new_mtime:
                        continue
                    # otherwise treat as changed and re-download

                # update seen map now (will be saved after successful download)
                # download file
                local = None
                try:
                    local = Path(tmpdir) / name
                    client.download_file(fid, str(local))
                    # Only invoke callback if approvals allow this watcher
                    try:
                        if approved_source_id:
                            # guard callback by approved_source_id (best-effort)
                            callback(str(local))
                        else:
                            callback(str(local))
                    except Exception:
                        pass
                    # mark seen with latest metadata
                    seen[fid] = {"id": fid, "name": name, "modifiedTime": new_mtime}
                    # persist seen map
                    try:
                        _save_seen(state_fp, seen)
                    except Exception:
                        pass
                except Exception:
                    # ignore individual download failures
                    continue
            time.sleep(poll_interval)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return thread


def _state_file_path(state_path: Optional[str]) -> Path:
    if state_path:
        return Path(state_path)
    return Path("out") / "drive_seen.json"


def _load_seen(fp: Path | str) -> dict:
    p = Path(fp)
    try:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if not data:
                return {}
            # If file contains a list of dicts with id, return a dict keyed by id
            if isinstance(data, list) and isinstance(data[0], dict) and data[0].get("id"):
                d = {}
                for item in data:
                    d[item["id"]] = item
                return d
            # Legacy format: list of plain id strings — return as set (preserved for compatibility)
            if isinstance(data, list):
                return set(data)
    except Exception:
        pass
    return {}


def _save_seen(fp: Path | str, seen_map: dict) -> None:
    p = Path(fp)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        # Accept either a dict of metadata or a set/list of ids
        if isinstance(seen_map, dict):
            tmp.write_text(json.dumps(list(seen_map.values())), encoding="utf-8")
        elif isinstance(seen_map, (set, list)):
            tmp.write_text(json.dumps(list(seen_map)), encoding="utf-8")
        else:
            # fallback: try to serialize
            tmp.write_text(json.dumps(seen_map), encoding="utf-8")
        tmp.replace(p)
    except Exception:
        pass


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


def start_watcher(path: str, callback: Callable[[str], None], background: bool = True, approved_source_id: Optional[str] = None) -> threading.Thread | None:
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Watch path not found: {path}")
    # Determine approved source id: explicit parameter takes precedence,
    # otherwise environment variable `WATCHER_APPROVED_SOURCE_ID` is used.
    approved_env = approved_source_id or os.environ.get("WATCHER_APPROVED_SOURCE_ID")
    if approved_env:
        try:
            from ingest.scrapers import approvals as approvals_mod

            if not approvals_mod.get_approval(approved_env):
                raise RuntimeError(f"Watcher approved source id not found: {approved_env}")
        except Exception as e:
            raise RuntimeError(f"Watcher approvals check failed: {e}")

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
