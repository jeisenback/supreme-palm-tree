"""ingest.scrapers package - simple scraper PoC."""

from .event_scraper import EventScraper
from .job_scraper import JobScraper
from .partner_scraper import PartnerScraper

__all__ = ["EventScraper", "JobScraper", "PartnerScraper"]
