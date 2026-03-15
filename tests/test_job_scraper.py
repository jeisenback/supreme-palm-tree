import responses

from ingest.scrapers.job_scraper import JobScraper

sample_html = """
<html>
  <body>
    <h1 class="job-title">Community Organizer</h1>
    <div class="job-org">Local Nonprofit</div>
    <div class="job-loc">Knoxville, TN</div>
    <div class="job-posted">2026-03-01</div>
    <div class="job-desc">Support community programs.</div>
  </body>
</html>
"""


@responses.activate
def test_job_scraper_parse_and_scrape():
    url = "https://example.org/jobs/1"
    responses.add(responses.GET, url, body=sample_html, status=200)
    selectors = {
        "title": ".job-title",
        "org": ".job-org",
        "location": ".job-loc",
        "posted": ".job-posted",
        "description": ".job-desc",
    }
    s = JobScraper(rate_limit_seconds=0, respect_robots=False)
    data = s.scrape(url, selectors)
    assert data["title"] == "Community Organizer"
    assert data["organization"] == "Local Nonprofit"
    assert data["location"] == "Knoxville, TN"
    assert data["posted"] == "2026-03-01"
    assert data["description"] == "Support community programs."
    assert data["source_url"] == url
