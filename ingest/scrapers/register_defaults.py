"""Register a couple of sample sources (PoC).

This helper is intended for tests and demos to populate the registry with
example job and partner source configs.
"""
from __future__ import annotations

from .scraper_registry import register_source


def register_default_sources() -> None:
    register_source(
        "sample_job",
        "https://example.org/jobs/1",
        parser="job",
        selectors={
            "title": ".job-title",
            "org": ".job-org",
            "location": ".job-loc",
            "posted": ".job-posted",
            "description": ".job-desc",
        },
    )

    register_source(
        "sample_partner",
        "https://example.org/partners/1",
        parser="partner",
        selectors={"name": ".partner-name", "desc": ".partner-desc"},
    )
