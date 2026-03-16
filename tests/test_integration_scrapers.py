import os
import sys

# ensure project root on sys.path when running tests directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def test_event_scraper_integration_with_stub(monkeypatch):
    """Integration-style test: stub HTTP response and ensure scheduler integrates."""
    from ingest.scrapers import scraper_registry, approvals
    from agents import scheduler

    url = "https://example.test/events/1"
    html = """
    <html>
      <body>
        <div class="ev-title">Community Meetup</div>
        <div class="ev-date">2026-04-01</div>
        <div class="ev-loc">Town Hall</div>
      </body>
    </html>
    """

    # stub registry to return our test source
    monkeypatch.setattr(scraper_registry, "list_sources", lambda: [
        {"id": "evt1", "url": url, "parser": "event", "selectors": {"title": ".ev-title", "date": ".ev-date", "location": ".ev-loc"}},
    ])

    # approve the source
    monkeypatch.setattr(approvals, "get_approval", lambda sid: {"id": "evt1", "allowed_paths": ["/events"], "rate_limit": 0})

    # stub requests.get used by BaseScraper.fetch
    class FakeResp:
        def __init__(self, text):
            self.text = text
            self.status_code = 200

        def raise_for_status(self):
            return None

    def fake_get(u, timeout=10):
        assert u == url
        return FakeResp(html)

    monkeypatch.setattr("requests.get", fake_get)

    called = {}

    def fake_integrate(item, src):
        called["item"] = item
        called["src"] = src

    monkeypatch.setattr("ingest.scrapers.integrate.integrate_scraped_item", fake_integrate)

    # run the scheduler scrape implementation directly
    scheduler._scrape_all_impl()

    assert called.get("src") == "evt1"
    it = called.get("item")
    assert it and it.get("title") == "Community Meetup"
    assert it.get("date") == "2026-04-01"
    assert it.get("location") == "Town Hall"
