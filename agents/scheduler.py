"""Simple in-process scheduler for periodic jobs (PoC).

Provides a tiny job registry and a background runner that executes registered
callables at a fixed interval. This is intentionally lightweight and suitable
for local demos or as a foundation for wiring APScheduler/cron later.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict


@dataclass
class Job:
    name: str
    func: Callable[[], None]
    interval_seconds: int
    last_run: float = field(default=0.0)


_JOBS: Dict[str, Job] = {}

_runner_thread: threading.Thread | None = None
_stop_event: threading.Event | None = None


def register_job(name: str, func: Callable[[], None], interval_seconds: int) -> None:
    """Register a job to run approximately every `interval_seconds`.

    If a job with the same name exists it will be replaced.
    """
    _JOBS[name] = Job(name=name, func=func, interval_seconds=interval_seconds)


def unregister_job(name: str) -> None:
    _JOBS.pop(name, None)


def list_jobs() -> dict:
    return {n: (j.interval_seconds, j.last_run) for n, j in _JOBS.items()}


def _job_runner(poll_interval: float = 1.0) -> None:
    global _stop_event
    while not _stop_event.is_set():
        now = time.time()
        for job in list(_JOBS.values()):
            try:
                if now - job.last_run >= job.interval_seconds:
                    job.last_run = now
                    threading.Thread(target=_run_job_safe, args=(job,)).start()
            except Exception:
                # never let one job crash the loop
                print(f"Error scheduling job {job.name}")
        _stop_event.wait(poll_interval)


def _run_job_safe(job: Job) -> None:
    try:
        print(f"[{datetime.utcnow().isoformat()}] Running job: {job.name}")
        job.func()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Job {job.name} failed: {exc}")


def start(poll_interval: float = 1.0) -> None:
    """Start the scheduler background thread."""
    global _runner_thread, _stop_event
    if _runner_thread and _runner_thread.is_alive():
        return
    _stop_event = threading.Event()
    _runner_thread = threading.Thread(target=_job_runner, args=(poll_interval,), daemon=True)
    _runner_thread.start()


def stop() -> None:
    """Stop the scheduler background thread and wait for it to finish."""
    global _runner_thread, _stop_event
    if _stop_event:
        _stop_event.set()
    if _runner_thread:
        _runner_thread.join(timeout=5.0)
    _runner_thread = None
    _stop_event = None


def run_once() -> None:
    """Run each registered job once (synchronously)."""
    for job in list(_JOBS.values()):
        _run_job_safe(job)


def register_default_jobs() -> None:
    """Register a couple of PoC jobs: scrape all sources and generate an agenda.

    Jobs are registered but not started automatically. Users should call
    `start()` to run the background scheduler.
    """
    # Import inside function to avoid heavy imports at module import time
    try:  # pragma: no cover - integration glue
        from ingest.scrapers.scraper_registry import list_sources
        from ingest.scrapers import EventScraper, JobScraper, PartnerScraper
        from ingest.scrapers.integrate import integrate_scraped_item
        from agents.skills.president import generate_agenda_with_llm
        from ingest.storage import store_conversion
        from datetime import date

        def _scrape_all() -> None:
            sources = list_sources()
            parser_map = {
                "event": EventScraper,
                "job": JobScraper,
                "partner": PartnerScraper,
            }
            for s in sources:
                parser = s.get("parser")
                cls = parser_map.get(parser)
                if not cls:
                    print(f"No parser for {parser} (source {s.get('id')})")
                    continue
                try:
                    scr = cls(rate_limit_seconds=0, respect_robots=False)
                    item = scr.scrape(s.get("url"), s.get("selectors", {}))
                    integrate_scraped_item(item, s.get("id"))
                except Exception as e:  # pragma: no cover - runtime integration
                    print(f"Error scraping {s.get('id')}: {e}")

        def _generate_agenda() -> None:
            notes = {"title": "Scheduled Agenda", "date": str(date.today()), "summary": "Auto-generated agenda."}
            md = generate_agenda_with_llm(notes)
            store_conversion(md, {"source": "scheduler"}, {}, "agenda_scheduled", "out")

        register_job("scrape_all_sources", _scrape_all, interval_seconds=60 * 60 * 24)
        register_job("generate_weekly_agenda", _generate_agenda, interval_seconds=60 * 60 * 24 * 7)
    except Exception:  # pragma: no cover - best-effort registration
        # If dependencies aren't available (tests, import-time), skip registration
        print("Skipping default job registration (dependencies missing)")
