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
