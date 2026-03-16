"""Register a couple of sample sources (PoC).

This helper is intended for tests and demos to populate the registry with
example job and partner source configs.
"""
from __future__ import annotations

from .scraper_registry import register_source
from .approvals import list_approved


def register_default_sources() -> None:
    # Only register default sources if they are present in the approvals list.
    approved = {d.get("id") for d in list_approved()}

    if "sample_job" in approved:
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

    if "sample_partner" in approved:
        register_source(
            "sample_partner",
            "https://example.org/partners/1",
            parser="partner",
            selectors={"name": ".partner-name", "desc": ".partner-desc"},
        )
