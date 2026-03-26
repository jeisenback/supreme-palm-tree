import os
import json
import time
from pathlib import Path

from agents import watcher


def test_start_watcher_rejects_unapproved(tmp_path):
    d = tmp_path / "watchdir"
    d.mkdir()
    # ensure no approvals for this id
    try:
        watcher.start_watcher(str(d), lambda p: None, approved_source_id="no-such-id")
        assert False, "Expected RuntimeError for unapproved id"
    except RuntimeError:
        pass


def test_start_watcher_accepts_approved(tmp_path, monkeypatch):
    d = tmp_path / "watchdir"
    d.mkdir()
    # prepare approvals file with the id
    appr_file = tmp_path / "approved.yaml"
    data = [{"id": "watcher-cli-test", "name": "Test"}]
    appr_file.write_text(json.dumps(data), encoding="utf-8")
    # point approvals module to this path
    import ingest.scrapers.approvals as approvals_mod

    monkeypatch.setattr(approvals_mod, "_PATH", appr_file)

    th = watcher.start_watcher(str(d), lambda p: None, background=True, approved_source_id="watcher-cli-test")
    assert th is not None
    # stop thread/observer if possible
    try:
        if hasattr(th, "stop"):
            th.stop()
        if hasattr(th, "join"):
            th.join(timeout=0.5)
    except Exception:
        pass
