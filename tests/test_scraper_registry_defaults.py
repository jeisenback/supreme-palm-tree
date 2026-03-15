from ingest.scrapers.register_defaults import register_default_sources
from ingest.scrapers.scraper_registry import get_source


def test_register_defaults_populates_registry():
    register_default_sources()
    job = get_source("sample_job")
    partner = get_source("sample_partner")
    assert job is not None and job["id"] == "sample_job"
    assert partner is not None and partner["id"] == "sample_partner"
