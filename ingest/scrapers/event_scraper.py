from __future__ import annotations

import re
import time
import urllib.parse
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

# ---------------------------------------------------------------------------
# MemberNova-specific helpers
# ---------------------------------------------------------------------------

_EMOJI_SPLIT = re.compile(r"[\U0001f4c5\U0001f4cd\U0001f399\U0001f4cc]")

# MemberNova listing URL template (Cards view renders full event list in one
# page when a date range is supplied).
_MN_LISTING_TMPL = (
    "{base}/Events/Cards?SearchTypes=None&From={from_date}&To={to_date}"
)

# web.membernova.com hosts the individual event detail pages.
_MN_DETAIL_HOST = "web.membernova.com"


def _after_emoji(emoji: str, text: str) -> str:
    idx = text.find(emoji)
    if idx == -1:
        return ""
    rest = text[idx + len(emoji) :].lstrip("\ufe0f").strip()
    m = _EMOJI_SPLIT.search(rest)
    return (rest[: m.start()] if m else rest).strip()


def _presenter_from_title(title: str) -> str:
    m = re.search(r"\bwith\s+(.+)$", title, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_membernova_event(html: str, url: str) -> Dict[str, Any]:
    """Parse a single MemberNova event detail page into a structured dict."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.h1.get_text(strip=True) if soup.h1 else ""

    # Structured date/time from h4.page-description
    h4 = soup.find("h4", class_="page-description")
    if h4:
        for span in h4.find_all("span"):
            span.decompose()
        date_str = h4.get_text(" ", strip=True)
    else:
        date_str = ""

    # Emoji summary paragraph (present on rich/speaker events)
    summary_p = ""
    for p in soup.find_all("p"):
        if "\U0001f4c5" in p.get_text():
            summary_p = p.get_text(strip=True)
            break

    location = _after_emoji("\U0001f4cd", summary_p) or "Virtual"
    presenter = _after_emoji("\U0001f399", summary_p) or _presenter_from_title(title)
    host = _after_emoji("\U0001f4cc", summary_p)

    # Bullet-point agenda/description items (skip nav li elements)
    nav_ids: set[int] = set()
    for el in soup.find_all(["nav", "ul"]):
        if any(c in el.get("class", []) for c in ("navbar-nav", "nav")):
            nav_ids.add(id(el))

    _nav_skip = {"Home", "Governance", "Membership", "Certification", "CAREERS"}
    bullets: list[str] = []
    for li in soup.find_all("li"):
        if any(id(p) in nav_ids for p in li.parents if hasattr(p, "name")):
            continue
        if any(p.name == "nav" for p in li.parents if hasattr(p, "name")):
            continue
        t = li.get_text(strip=True)
        if t and len(t) > 5 and t not in _nav_skip:
            bullets.append(t)

    # h3 section bodies (rich events)
    sections: dict[str, str] = {}
    for h3 in soup.find_all("h3"):
        heading = h3.get_text(strip=True)
        parts: list[str] = []
        for sib in h3.next_siblings:
            if hasattr(sib, "name") and sib.name == "h3":
                break
            if hasattr(sib, "get_text"):
                t = sib.get_text(" ", strip=True)
                if t:
                    parts.append(t)
        sections[heading] = " ".join(parts)

    # Short span description used by simple (non-rich) events
    short_desc = ""
    for span in soup.find_all("span"):
        if span.get("class"):
            continue
        t = span.get_text(strip=True)
        if t and len(t) > 20 and "\U0001f4c5" not in t:
            short_desc = t
            break

    return {
        "url": url,
        "title": title,
        "date": date_str,
        "location": location,
        "presenter": presenter,
        "host": host,
        "description_bullets": bullets,
        "overview": sections.get("Session Overview", "") or short_desc,
        "learning_objectives": sections.get("Learning Objectives", ""),
        "pdu_credits": sections.get("Professional Development Credits", ""),
        "about_presenter": sections.get("About the Presenter", ""),
    }


# ---------------------------------------------------------------------------
# EventScraper
# ---------------------------------------------------------------------------


class EventScraper(BaseScraper):
    """Event scraper supporting both static CSS-selector and headless modes.

    Static mode (original)
    ----------------------
    ``scrape(url, selectors)`` — fetches with ``requests`` and extracts fields
    via CSS selectors.  Works for plain-HTML sites.

    Headless / MemberNova mode
    --------------------------
    ``scrape_membernova(base_url, from_date, to_date)`` — launches headless
    Chromium via Playwright, fetches the Cards listing for the given date
    range, follows each event detail link, and returns a list of structured
    event dicts parsed by :func:`parse_membernova_event`.

    Playwright is imported lazily so the package stays importable without it
    installed.
    """

    # ------------------------------------------------------------------
    # Static (requests-based) path — unchanged from original
    # ------------------------------------------------------------------

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
            "date": _select("date"),
            "location": _select("location"),
        }

    def scrape(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        html = self.fetch(url)
        data = self.parse(html, selectors)
        data.update({"source_url": url})
        return data

    # ------------------------------------------------------------------
    # Headless MemberNova path
    # ------------------------------------------------------------------

    def scrape_membernova(
        self,
        base_url: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        timeout_ms: int = 30_000,
        extra_wait_ms: int = 3_000,
    ) -> List[Dict[str, Any]]:
        """Scrape all events from a MemberNova chapter site.

        Parameters
        ----------
        base_url:
            Root URL of the chapter site, e.g. ``https://easttennessee.iiba.org``.
        from_date / to_date:
            Date range for the listing page.  Defaults to the past two years
            through today.
        timeout_ms:
            Per-page Playwright navigation timeout in milliseconds.
        extra_wait_ms:
            Additional wait after ``networkidle`` to allow late JS rendering.

        Returns
        -------
        list of event dicts, sorted oldest-first.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "playwright is required for headless scraping. "
                "Install it with: pip install playwright && python -m playwright install chromium"
            ) from exc

        today = date.today()
        if to_date is None:
            to_date = today
        if from_date is None:
            from_date = today.replace(year=today.year - 2)

        base_url = base_url.rstrip("/")
        listing_url = _MN_LISTING_TMPL.format(
            base=base_url,
            from_date=from_date.strftime("%Y/%m/%d"),
            to_date=to_date.strftime("%Y/%m/%d"),
        )

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = ctx.new_page()

            # --- Step 1: fetch listing ---
            self._headless_goto(page, listing_url, timeout_ms, extra_wait_ms)
            detail_links = self._extract_detail_links(page.content())

            # --- Step 2: fetch each detail page ---
            events: list[dict] = []
            for url in detail_links:
                # Respect rate limit between requests
                time.sleep(max(self.rate_limit, 0.5))
                try:
                    self._headless_goto(page, url, timeout_ms, extra_wait_ms)
                    ev = parse_membernova_event(page.content(), url)
                    if ev["title"]:
                        events.append(ev)
                except Exception:  # noqa: BLE001
                    pass  # skip pages that 404 or time out

            browser.close()

        events.sort(key=lambda e: self._parse_date(e["date"]))
        return events

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _headless_goto(page: Any, url: str, timeout_ms: int, extra_wait_ms: int) -> None:
        page.goto(url, timeout=timeout_ms, wait_until="networkidle")
        if extra_wait_ms > 0:
            page.wait_for_timeout(extra_wait_ms)

    @staticmethod
    def _extract_detail_links(html: str) -> List[str]:
        """Return deduplicated event detail URLs from a MemberNova listing page."""
        soup = BeautifulSoup(html, "html.parser")
        seen: set[str] = set()
        links: list[str] = []
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if (
                _MN_DETAIL_HOST in href
                and "/Events/" in href
                and "?" not in href
                and href not in seen
            ):
                seen.add(href)
                links.append(href)
        return links

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        m = re.match(r"(\w+ \d+, \d+)", date_str or "")
        if m:
            try:
                return datetime.strptime(m.group(1), "%b %d, %Y")
            except ValueError:
                pass
        return datetime.min
