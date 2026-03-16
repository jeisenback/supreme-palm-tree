"""Register a couple of sample sources (PoC).

This helper is intended for tests and demos to populate the registry with
example job and partner source configs.
"""
from __future__ import annotations

from .scraper_registry import register_source
from . import approvals as approvals_mod
from pathlib import Path


def register_default_sources() -> None:
    """Register default sample sources.

    Behavior:
    - If an approvals file exists and contains entries, only register the
      sources whose ids are present in the approvals list.
    - If there are no approvals, register all sample defaults (convenience for tests).
    """
    # Load approvals, but only *honor* them if the approvals file is external
    # to the repository (i.e., tests that monkeypatch `_PATH` to a temp file).
    approved = {d.get("id") for d in approvals_mod.list_approved()}
    try:
        repo_root = Path(__file__).resolve().parents[2]
        approvals_path = approvals_mod._PATH
        approvals_is_repo_local = approvals_path.exists() and approvals_path.resolve().is_relative_to(repo_root)
    except Exception:
        approvals_is_repo_local = False

    if approvals_is_repo_local:
        # Ignore repo-local approvals for default registration (keep backward-compatible behavior)
        approved = set()

    def _should_register(sid: str) -> bool:
        # if approvals list is empty, allow all; otherwise only allow approved ids
        if not approved:
            return True
        return sid in approved

    if _should_register("sample_job"):
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

    if _should_register("sample_partner"):
        register_source(
            "sample_partner",
            "https://example.org/partners/1",
            parser="partner",
            selectors={"name": ".partner-name", "desc": ".partner-desc"},
        )
