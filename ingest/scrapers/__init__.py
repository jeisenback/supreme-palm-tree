"""ingest.scrapers package - simple scraper PoC."""

from .event_scraper import EventScraper
from .job_scraper import JobScraper

__all__ = ["EventScraper", "JobScraper"]
