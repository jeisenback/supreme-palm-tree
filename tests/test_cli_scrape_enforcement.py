import os
import sys

# ensure project root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import importlib
from ingest.scrapers import scraper_registry, approvals
from agents import agents_cli


def test_cli_scrape_skips_unapproved(monkeypatch):
    monkeypatch.setattr(scraper_registry, 'get_source', lambda sid: {"id": "x1", "url": "https://example.org/", "parser": "event", "selectors": {}})
    importlib.reload(approvals)
    monkeypatch.setattr(approvals, 'get_approval', lambda sid: None)

    rc = agents_cli.main(["scrape", "--source-id", "x1"])
    assert rc == 14


def test_cli_scrape_allows_and_integrates(monkeypatch):
    monkeypatch.setattr(scraper_registry, 'get_source', lambda sid: {"id": "x2", "url": "https://example.org/p", "parser": "event", "selectors": {}})
    importlib.reload(approvals)
    monkeypatch.setattr(approvals, 'get_approval', lambda sid: {"id": "x2", "allowed_paths": ["/p"], "rate_limit": 0.0})

    called = {}

    class FakeScraper:
        def __init__(self, rate_limit_seconds=0, respect_robots=False):
            pass

        def scrape(self, url, selectors):
            return {"type": "event", "source_url": url}

    monkeypatch.setattr("ingest.scrapers.EventScraper", FakeScraper)
    monkeypatch.setattr("ingest.scrapers.integrate.integrate_scraped_item", lambda item, sid: called.update({"sid": sid, "item": item}))

    rc = agents_cli.main(["scrape", "--source-id", "x2"])
    assert rc == 0
    assert called.get("sid") == "x2"
