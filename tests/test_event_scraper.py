import responses

from ingest.scrapers.event_scraper import EventScraper


sample_html = """
<html>
  <body>
    <h1 class="title">Event A</h1>
    <div class="date">2026-04-01</div>
    <div class="loc">Online</div>
  </body>
</html>
"""


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
