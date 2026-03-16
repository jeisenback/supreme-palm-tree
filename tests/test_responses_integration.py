import os
import sys

# ensure project root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import responses
from ingest.scrapers import scraper_registry, approvals
from agents import scheduler


@responses.activate
def test_event_scraper_with_responses(monkeypatch):
    url = "https://fixtures.test/events/1"
    html = """
    <html>
      <body>
        <div class="ev-title">Responses Meetup</div>
        <div class="ev-date">2026-05-01</div>
        <div class="ev-loc">Community Center</div>
      </body>
    </html>
    """

    responses.add(responses.GET, url, body=html, status=200, content_type="text/html")

    # stub registry to return our test source
    monkeypatch.setattr(scraper_registry, "list_sources", lambda: [
        {"id": "r1", "url": url, "parser": "event", "selectors": {"title": ".ev-title", "date": ".ev-date", "location": ".ev-loc"}},
    ])

    # approve the source
    monkeypatch.setattr(approvals, "get_approval", lambda sid: {"id": "r1", "allowed_paths": ["/events"], "rate_limit": 0})

    called = {}

    def fake_integrate(item, src):
        called["item"] = item
        called["src"] = src

    monkeypatch.setattr("ingest.scrapers.integrate.integrate_scraped_item", fake_integrate)

    scheduler._scrape_all_impl()

    assert called.get("src") == "r1"
    it = called.get("item")
    assert it and it.get("title") == "Responses Meetup"
    assert it.get("date") == "2026-05-01"
    assert it.get("location") == "Community Center"
