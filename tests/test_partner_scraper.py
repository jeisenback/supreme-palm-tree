import responses

from ingest.scrapers.partner_scraper import PartnerScraper

sample_html = """
<html>
  <body>
    <h1 class="partner-name">Community Center</h1>
    <a class="partner-website" href="https://community.example.org">site</a>
    <div class="partner-desc">Local community hub offering programs.</div>
    <div class="partner-contact">info@community.example.org</div>
  </body>
</html>
"""


@responses.activate
def test_partner_scraper_parse_and_scrape():
    url = "https://example.org/partners/1"
    responses.add(responses.GET, url, body=sample_html, status=200)
    selectors = {
        "name": ".partner-name",
        "website": ".partner-website",
        "desc": ".partner-desc",
        "contact": ".partner-contact",
    }
    s = PartnerScraper(rate_limit_seconds=0, respect_robots=False)
    data = s.scrape(url, selectors)
    assert data["name"] == "Community Center"
    assert data["website"] == "site"
    assert data["description"] == "Local community hub offering programs."
    assert data["contact"] == "info@community.example.org"
    assert data["source_url"] == url
