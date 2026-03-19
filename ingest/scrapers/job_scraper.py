from __future__ import annotations

from typing import Any, Dict

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper


class JobScraper(BaseScraper):
    """Simple job posting scraper.

    PoC accepts a `selectors` dict with keys: `title`, `org`, `location`,
    `posted`, and `description`.
    """

    def parse(self, html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")

        def _select(key: str) -> Any:
            sel = selectors.get(key)
            if not sel:
                return None
            el = soup.select_one(sel)
            return el.get_text(strip=True) if el else None

        return {
            "title": _select("title"),
            "organization": _select("org"),
            "location": _select("location"),
            "posted": _select("posted"),
            "description": _select("description"),
        }

    def scrape(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        html = self.fetch(url)
        data = self.parse(html, selectors)
        data.update({"source_url": url})
        return data
