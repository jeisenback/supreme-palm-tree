from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import responses

from ingest.scrapers.event_scraper import EventScraper, parse_membernova_event


sample_html = """
<html>
  <body>
    <h1 class="title">Event A</h1>
    <div class="date">2026-04-01</div>
    <div class="loc">Online</div>
  </body>
</html>
"""

# Minimal MemberNova listing page containing one event detail link
MN_LISTING_HTML = """
<html><body>
  <a href="https://web.membernova.com/400592/Events/test-event">Test Event</a>
</body></html>
"""

# Minimal MemberNova event detail page
MN_DETAIL_HTML = """
<html><body>
  <h1>Test Event</h1>
  <h4 class="page-description">
    Apr 01, 2026  7:00 PM - 8:00 PM
    <span class="tooltip-text help-message">Eastern Daylight Time</span>
  </h4>
  <p>\U0001f4c5April 1, 2026\U0001f4cdVirtual Webinar\U0001f399 Presented by Jane Doe</p>
  <h3>Session Overview</h3>
  <p>An introduction to BA techniques.</p>
  <h3>Learning Objectives</h3>
  <li>Understand BA fundamentals</li>
</body></html>
"""


# ---------------------------------------------------------------------------
# Original static-scrape test (unchanged behaviour)
# ---------------------------------------------------------------------------


@responses.activate
def test_event_scraper_parse_and_scrape():
    url = "https://example.org/events/1"
    responses.add(responses.GET, url, body=sample_html, status=200)
    selectors = {"title": ".title", "date": ".date", "location": ".loc"}
    s = EventScraper(rate_limit_seconds=0, respect_robots=False)
    data = s.scrape(url, selectors)
    assert data["title"] == "Event A"
    assert data["date"] == "2026-04-01"
    assert data["location"] == "Online"
    assert data["source_url"] == url


# ---------------------------------------------------------------------------
# parse_membernova_event unit tests (pure HTML parsing, no network)
# ---------------------------------------------------------------------------


def test_parse_membernova_event_fields():
    ev = parse_membernova_event(MN_DETAIL_HTML, "https://web.membernova.com/400592/Events/test-event")
    assert ev["title"] == "Test Event"
    assert "Apr 01, 2026" in ev["date"]
    assert ev["location"] == "Virtual Webinar"
    assert "Jane Doe" in ev["presenter"]
    assert ev["overview"] == "An introduction to BA techniques."
    assert "Understand BA fundamentals" in ev["learning_objectives"]


def test_parse_membernova_event_presenter_from_title():
    html = """
    <html><body>
      <h1>Great Talk with Alice Smith</h1>
      <h4 class="page-description">Jan 10, 2025  7:00 PM - 8:00 PM</h4>
    </body></html>
    """
    ev = parse_membernova_event(html, "https://web.membernova.com/400592/Events/great-talk")
    assert ev["presenter"] == "Alice Smith"


def test_parse_membernova_event_virtual_default():
    html = """
    <html><body>
      <h1>Simple Event</h1>
      <h4 class="page-description">Mar 01, 2025  6:00 PM - 7:00 PM</h4>
    </body></html>
    """
    ev = parse_membernova_event(html, "https://web.membernova.com/400592/Events/simple")
    assert ev["location"] == "Virtual"


# ---------------------------------------------------------------------------
# scrape_membernova integration test (Playwright mocked)
# ---------------------------------------------------------------------------


def _make_page_mock(listing_html: str, detail_html: str) -> MagicMock:
    """Return a mock Playwright page that serves listing then detail HTML."""
    call_count = [0]

    def fake_content():
        # First call = listing page; subsequent calls = detail page
        if call_count[0] == 0:
            call_count[0] += 1
            return listing_html
        return detail_html

    page = MagicMock()
    page.content.side_effect = fake_content
    return page


def test_scrape_membernova_returns_events():
    page = _make_page_mock(MN_LISTING_HTML, MN_DETAIL_HTML)

    ctx = MagicMock()
    ctx.new_page.return_value = page

    browser = MagicMock()
    browser.new_context.return_value = ctx

    pw_instance = MagicMock()
    pw_instance.chromium.launch.return_value = browser

    pw_ctx_manager = MagicMock()
    pw_ctx_manager.__enter__ = MagicMock(return_value=pw_instance)
    pw_ctx_manager.__exit__ = MagicMock(return_value=False)

    with patch("ingest.scrapers.event_scraper.sync_playwright", return_value=pw_ctx_manager, create=True):
        # Also patch the lazy import inside scrape_membernova
        with patch.dict("sys.modules", {"playwright.sync_api": MagicMock(sync_playwright=lambda: pw_ctx_manager)}):
            scraper = EventScraper(rate_limit_seconds=0, respect_robots=False)
            events = scraper.scrape_membernova(
                "https://easttennessee.iiba.org",
                from_date=date(2024, 1, 1),
                to_date=date(2026, 3, 17),
            )

    assert len(events) == 1
    assert events[0]["title"] == "Test Event"
    assert "Apr 01, 2026" in events[0]["date"]
