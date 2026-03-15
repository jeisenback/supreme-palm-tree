import tempfile
from pathlib import Path

from ingest.scrapers import approvals


def test_approve_and_revoke(tmp_path: Path):
    # redirect approvals path to tmp file
    approvals._PATH = tmp_path / "approved.yaml"

    # ensure clean state
    try:
        (tmp_path / "approved.yaml").unlink()
    except Exception:
        pass

    # add approval
    approvals.approve_source("source-123", {"name": "Test Source"})
    items = approvals.list_approved()
    assert any(i.get("id") == "source-123" for i in items)

    # revoke
    approvals.revoke_source("source-123")
    items = approvals.list_approved()
    assert all(i.get("id") != "source-123" for i in items)
