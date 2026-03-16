import os
import sys
import importlib
import urllib.parse

# Ensure project root is on sys.path for imports when running this test directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def test_skips_unapproved_source(monkeypatch):
    # source present but not approved -> should be skipped (scraper not invoked)
    from ingest.scrapers import scraper_registry, approvals
    from agents import scheduler

    monkeypatch.setattr(scraper_registry, "list_sources", lambda: [
        {"id": "s1", "url": "https://example.org/forbidden", "parser": "event", "selectors": {}},
    ])
    importlib.reload(approvals)
    monkeypatch.setattr(approvals, "get_approval", lambda sid: None)

    class FakeScraper:
        def __init__(self, rate_limit_seconds=0, respect_robots=False):
            pass

        def scrape(self, url, selectors):
            raise AssertionError("Scraper should not be invoked for unapproved source")

    monkeypatch.setattr("ingest.scrapers.EventScraper", FakeScraper)

    # Should run without invoking the fake scraper
    scheduler._scrape_all_impl()


def test_enforces_allowed_paths_and_rate_limit(monkeypatch):
    # approved source with allowed_paths that doesn't match should be skipped
    from ingest.scrapers import scraper_registry, approvals
    from agents import scheduler

    monkeypatch.setattr(scraper_registry, "list_sources", lambda: [
        {"id": "s2", "url": "https://example.org/forbidden/path", "parser": "event", "selectors": {}},
    ])

    importlib.reload(approvals)
    monkeypatch.setattr(approvals, "get_approval", lambda sid: {"id": "s2", "allowed_paths": ["/allowed"], "rate_limit": 0.0})

    class FakeScraper2:
        def __init__(self, rate_limit_seconds=0, respect_robots=False):
            pass

        def scrape(self, url, selectors):
            raise AssertionError("Scraper should not be invoked when path not allowed")

    monkeypatch.setattr("ingest.scrapers.EventScraper", FakeScraper2)

    scheduler._scrape_all_impl()


def test_allows_when_path_matches_and_calls_integrate(monkeypatch):
    # approved source with allowed_paths that matches -> should invoke scraper and integrate
    from ingest.scrapers import scraper_registry, approvals
    from agents import scheduler

    monkeypatch.setattr(scraper_registry, "list_sources", lambda: [
        {"id": "s3", "url": "https://example.org/allowed/page", "parser": "event", "selectors": {}},
    ])

    importlib.reload(approvals)
    monkeypatch.setattr(approvals, "get_approval", lambda sid: {"id": "s3", "allowed_paths": ["/allowed"], "rate_limit": 0.0})

    called = {}

    class FakeScraper3:
        def __init__(self, rate_limit_seconds=0, respect_robots=False):
            pass

        def scrape(self, url, selectors):
            return {"type": "event", "source_url": url}

    def fake_integrate(item, source_id):
        called["item"] = item
        called["sid"] = source_id

    monkeypatch.setattr("ingest.scrapers.EventScraper", FakeScraper3)
    monkeypatch.setattr("ingest.scrapers.integrate.integrate_scraped_item", fake_integrate)

    scheduler._scrape_all_impl()

    assert called.get("sid") == "s3"
    assert called.get("item") and called["item"].get("source_url") == "https://example.org/allowed/page"
