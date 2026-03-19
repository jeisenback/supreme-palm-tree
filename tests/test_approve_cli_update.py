import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import importlib
from ingest.scrapers import approvals
from agents import agents_cli


def test_cli_update_and_remove_field(tmp_path, monkeypatch):
    # set approvals path to tmp file
    tmpfile = tmp_path / "approved.yaml"
    approvals._PATH = tmpfile

    # add initial approval via CLI add
    rc = agents_cli.main(["approve", "add", "u1", "--meta", '{"notes": "initial"}', "--rate-limit", "1.5"]) 
    assert rc == 0

    items = approvals.list_approved()
    assert any(i.get("id") == "u1" for i in items)

    # update metadata
    rc = agents_cli.main(["approve", "update", "u1", "--meta", '{"notes": "updated", "contact": "me@example.org"}' ])
    assert rc == 0
    obj = approvals.get_approval("u1")
    assert obj.get("notes") == "updated"
    assert obj.get("contact") == "me@example.org"

    # remove field
    rc = agents_cli.main(["approve", "remove-field", "u1", "notes"]) 
    assert rc == 0
    obj = approvals.get_approval("u1")
    assert "notes" not in obj
