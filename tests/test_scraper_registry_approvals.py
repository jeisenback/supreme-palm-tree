from pathlib import Path
import json

from ingest.scrapers import register_defaults, scraper_registry
from ingest.scrapers import approvals


def test_register_defaults_only_registers_approved(tmp_path, monkeypatch):
    # Point approvals to a temp file to avoid touching repo config
    tmp_file = tmp_path / "approved.yaml"
    monkeypatch.setattr(approvals, "_PATH", tmp_file)

    # write approvals containing only sample_job
    data = [{"id": "sample_job", "name": "Sample Job Site"}]
    # write as JSON for simplicity
    tmp_file.write_text(json.dumps(data), encoding="utf-8")

    # clear registry
    scraper_registry._REGISTRY.clear()

    # call register defaults; only sample_job should be registered
    register_defaults.register_default_sources()
    sources = scraper_registry.list_sources()
    ids = {s["id"] for s in sources}
    assert "sample_job" in ids
    assert "sample_partner" not in ids
