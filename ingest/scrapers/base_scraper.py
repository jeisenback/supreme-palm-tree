from __future__ import annotations

import time
import urllib.parse
import urllib.robotparser
from typing import Optional

import requests


class BaseScraper:
    """Minimal base scraper with robots.txt check and per-host rate limiting.

    This is a PoC implementation intended for tests and light scraping. It
    respects robots.txt where possible and enforces a simple per-host delay.
    """

    def __init__(self, rate_limit_seconds: float = 1.0, respect_robots: bool = True) -> None:
        self.rate_limit = float(rate_limit_seconds)
        self._last_request: dict[str, float] = {}
        self.respect_robots = bool(respect_robots)

    def _can_fetch(self, url: str) -> bool:
        if not self.respect_robots:
            return True

        try:
            parsed = urllib.parse.urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch("*", url)
        except Exception:
            # If robots.txt cannot be fetched/parsed, default to allowing
            return True

    def fetch(self, url: str, timeout: int = 10) -> Optional[str]:
        if not self._can_fetch(url):
            raise RuntimeError(f"Robots.txt disallows fetching {url}")

        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc
        last = self._last_request.get(host)
        if last is not None:
            elapsed = time.time() - last
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)

        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        self._last_request[host] = time.time()
        return resp.text
