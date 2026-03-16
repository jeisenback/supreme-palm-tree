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
import os
import urllib.parse

# optional observability hooks
try:  # pragma: no cover - exercised in integration
    from agents.observability import init_metrics_server, record_job_start, record_job_end
except Exception:  # pragma: no cover - import-time resilience for tests
    def init_metrics_server(port: int = 8000) -> None:  # type: ignore
        return

    def record_job_start(job_name: str) -> float:  # type: ignore
        import time

        return time.time()

    def record_job_end(job_name: str, start_ts: float, success: bool = True) -> None:  # type: ignore
        return
import json
from pathlib import Path
import sqlite3
from typing import Any
try:  # optional APScheduler integration
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    _HAS_APSCHEDULER = True
except Exception:
    _HAS_APSCHEDULER = False

# APScheduler instance (optional)
_apscheduler: "BackgroundScheduler" | None = None


@dataclass
class Job:
    name: str
    func: Callable[[], None]
    interval_seconds: int
    last_run: float = field(default=0.0)
    # retry configuration
    retries: int = field(default=0)
    retry_backoff_seconds: int = field(default=0)
    # runtime state
    retry_attempts: int = field(default=0)


_JOBS: Dict[str, Job] = {}

_runner_thread: threading.Thread | None = None
_stop_event: threading.Event | None = None


def register_job(
    name: str,
    func: Callable[[], None],
    interval_seconds: int,
    retries: int = 0,
    retry_backoff_seconds: int = 0,
    skip_persist: bool = False,
) -> None:
    """Register a job to run approximately every `interval_seconds`.

    If a job with the same name exists it will be replaced.
    """
    _JOBS[name] = Job(
        name=name,
        func=func,
        interval_seconds=interval_seconds,
        retries=retries,
        retry_backoff_seconds=retry_backoff_seconds,
    )
    # If APScheduler is available and running, also schedule the job there.
    try:
        global _apscheduler
        if _HAS_APSCHEDULER and _apscheduler is not None:
            # remove existing APScheduler job if present
            try:
                _apscheduler.remove_job(name)
            except Exception:
                pass

            # schedule a dispatcher that will call into our runtime job table
            _apscheduler.add_job(
                _apscheduler_dispatch,
                "interval",
                seconds=interval_seconds,
                args=[name],
                id=name,
                replace_existing=True,
            )
    except Exception:
        pass
    if not skip_persist:
        try:
            _save_state()
        except Exception:
            # best-effort persistence; do not break registration on failure
            pass


def schedule_one_off(name: str, func: Callable[[], None], delay_seconds: int) -> None:
    """Schedule a one-off job that runs after `delay_seconds` and then unregisters itself.

    The job name should be unique. The wrapper will unregister the job after running.
    """
    def _wrapper() -> None:
        try:
            func()
        finally:
            try:
                unregister_job(name)
            except Exception:
                pass

    register_job(name, _wrapper, interval_seconds=delay_seconds)

def unregister_job(name: str) -> None:
    _JOBS.pop(name, None)
    try:
        _save_state()
    except Exception:
        pass
    # also remove from APScheduler if present
    try:
        global _apscheduler
        if _HAS_APSCHEDULER and _apscheduler is not None:
            _apscheduler.remove_job(name)
    except Exception:
        pass


def list_jobs() -> dict:
    return {
        n: (
            j.interval_seconds,
            j.last_run,
            j.retries,
            j.retry_backoff_seconds,
            j.retry_attempts,
        )
        for n, j in _JOBS.items()
    }


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


def _apscheduler_dispatch(job_name: str) -> None:
    """Dispatcher used by APScheduler jobs to call our runtime job runner.

    APScheduler persists job schedule and will import this module path; the
    dispatcher looks up the live Job object in `_JOBS` and invokes
    `_run_job_safe` to preserve retry semantics.
    """
    job = _JOBS.get(job_name)
    if job is None:
        return
    # run in a separate thread to avoid blocking APScheduler worker
    threading.Thread(target=_run_job_safe, args=(job,), daemon=True).start()


def _run_job_safe(job: Job) -> None:
    try:
        print(f"[{datetime.utcnow().isoformat()}] Running job: {job.name}")
        start_ts = record_job_start(job.name)
        job.func()
        # reset retry attempts on success
        job.retry_attempts = 0
        try:
            _save_state()
        except Exception:
            pass
        record_job_end(job.name, start_ts, success=True)
    except Exception as exc:  # pragma: no cover - defensive
        try:
            record_job_end(job.name, start_ts, success=False)
        except Exception:
            pass
        print(f"Job {job.name} failed: {exc}")
        # schedule retry if configured
        try:
            job.retry_attempts = (job.retry_attempts or 0) + 1
            try:
                _save_state()
            except Exception:
                pass
            if job.retries and job.retry_attempts <= job.retries:
                backoff = int(job.retry_backoff_seconds or 0) * job.retry_attempts
                def _delayed_retry(j: Job, delay: int) -> None:
                    try:
                        time.sleep(delay)
                        _run_job_safe(j)
                    except Exception:
                        pass

                threading.Thread(target=_delayed_retry, args=(job, backoff), daemon=True).start()
            else:
                print(f"Job {job.name} exhausted retries ({job.retry_attempts}/{job.retries})")
        except Exception:
            pass


def start(poll_interval: float = 1.0) -> None:
    """Start the scheduler background thread."""
    global _runner_thread, _stop_event, _apscheduler
    if _runner_thread and _runner_thread.is_alive():
        return

    # If APScheduler is available, prefer it with an SQLAlchemy jobstore.
    if _HAS_APSCHEDULER:
        try:
            root = Path(__file__).resolve().parents[1]
            db_path = root / ".scheduler_jobs.db"
            jobstore = SQLAlchemyJobStore(url=f"sqlite:///{db_path}")
            _apscheduler = BackgroundScheduler(jobstores={"default": jobstore})
            _apscheduler.start()
            # restore persisted jobs into memory state and ensure APScheduler has them
            try:
                _load_state()
            except Exception:
                print("No persisted scheduler state loaded")
            # ensure APScheduler has entries for current _JOBS
            for name, job in list(_JOBS.items()):
                try:
                    # remove existing then add with current interval
                    try:
                        _apscheduler.remove_job(name)
                    except Exception:
                        pass
                    _apscheduler.add_job(
                        _apscheduler_dispatch,
                        "interval",
                        seconds=job.interval_seconds,
                        args=[name],
                        id=name,
                        replace_existing=True,
                    )
                except Exception:
                    pass
        except Exception:
            # fall back to in-process runner
            _apscheduler = None

    # Start in-process runner for environments without APScheduler
    if not _HAS_APSCHEDULER or _apscheduler is None:
        _stop_event = threading.Event()
        _runner_thread = threading.Thread(target=_job_runner, args=(poll_interval,), daemon=True)
        # Attempt to restore persisted jobs (best-effort)
        try:
            _load_state()
        except Exception:
            print("No persisted scheduler state loaded")
        # Optionally start metrics server if env var set
        try:
            port = int(os.environ.get("SCHEDULER_METRICS_PORT", "0") or 0)
            if port:
                init_metrics_server(port)
        except Exception:
            pass
        _runner_thread.start()


# --- Persistence helpers (simple PoC using JSON) --------------------------


def _state_path() -> Path:
    # store state at repository root as .scheduler_state.json
    root = Path(__file__).resolve().parents[1]
    return root / ".scheduler_state.json"


def _db_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / ".scheduler_jobs.db"


def _ensure_db() -> None:
    p = _db_path()
    try:
        conn = sqlite3.connect(str(p))
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS job_state (
                name TEXT PRIMARY KEY,
                last_run REAL,
                retry_attempts INTEGER
            )
            """
        )
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _db_set_state(name: str, last_run: float, retry_attempts: int) -> None:
    p = _db_path()
    try:
        conn = sqlite3.connect(str(p))
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO job_state (name, last_run, retry_attempts) VALUES (?, ?, ?)",
            (name, float(last_run or 0), int(retry_attempts or 0)),
        )
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _db_get_all() -> dict[str, dict[str, Any]]:
    p = _db_path()
    out: dict[str, dict[str, Any]] = {}
    if not p.exists():
        return out
    try:
        conn = sqlite3.connect(str(p))
        cur = conn.cursor()
        cur.execute("SELECT name, last_run, retry_attempts FROM job_state")
        for name, last_run, retry_attempts in cur.fetchall():
            out[name] = {"last_run": float(last_run or 0), "retry_attempts": int(retry_attempts or 0)}
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return out


def _save_state() -> None:
    data = []
    for j in _JOBS.values():
        data.append(
            {
                "name": j.name,
                "interval_seconds": j.interval_seconds,
                "last_run": j.last_run,
                "retries": j.retries,
                "retry_backoff_seconds": j.retry_backoff_seconds,
                "retry_attempts": j.retry_attempts,
            }
        )
    path = _state_path()
    try:
        path.write_text(json.dumps(data, indent=2))
    except Exception:
        # best-effort; ignore errors
        pass
    # Also persist runtime state into SQLite when APScheduler is available
    try:
        if _HAS_APSCHEDULER:
            _ensure_db()
            for j in _JOBS.values():
                _db_set_state(j.name, j.last_run, j.retry_attempts)
    except Exception:
        pass


def _load_state() -> None:
    path = _state_path()
    if not path.exists():
        return
    try:
        raw = path.read_text()
        data = json.loads(raw)
    except Exception:
        return
    for item in data:
        name = item.get("name")
        interval = int(item.get("interval_seconds", 0))
        if name and name not in _JOBS:
            factory = _KNOWN_JOB_FACTORIES.get(name)
            if factory:
                # restore retry config if present
                retries = int(item.get("retries", 0) or 0)
                backoff = int(item.get("retry_backoff_seconds", 0) or 0)
                register_job(name, factory, interval, retries=retries, retry_backoff_seconds=backoff, skip_persist=True)
                # restore runtime state from DB if available, else from JSON
                job = _JOBS.get(name)
                if job is not None:
                    # prefer DB state when APScheduler is used
                    try:
                        if _HAS_APSCHEDULER:
                            db_rows = _db_get_all()
                            row = db_rows.get(name)
                            if row is not None:
                                job.last_run = float(row.get("last_run", 0) or 0)
                                job.retry_attempts = int(row.get("retry_attempts", 0) or 0)
                                continue
                    except Exception:
                        pass
                    job.last_run = float(item.get("last_run", 0) or 0)
                    job.retry_attempts = int(item.get("retry_attempts", 0) or 0)
            else:
                print(f"Persisted job '{name}' found but no factory available; skipping")


# --- Known job implementations (moved from register_default_jobs inner scope) ---


def _scrape_all_impl() -> None:
    try:  # pragma: no cover - integration glue
        from ingest.scrapers.scraper_registry import list_sources
        from ingest.scrapers import EventScraper, JobScraper, PartnerScraper
        from ingest.scrapers.integrate import integrate_scraped_item
        from ingest.scrapers import approvals as approvals_mod

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
            sid = s.get("id")
            approval = approvals_mod.get_approval(sid)
            if not approval:
                print(f"Skipping unapproved source {sid}")
                continue

            # enforce allowed_paths if present
            allowed_paths = approval.get("allowed_paths")
            if allowed_paths:
                try:
                    parsed = urllib.parse.urlparse(s.get("url") or "")
                    path = parsed.path or "/"
                    if isinstance(allowed_paths, str):
                        allowed_list = [allowed_paths]
                    else:
                        allowed_list = list(allowed_paths)
                    if not any(path.startswith(ap) for ap in allowed_list):
                        print(f"URL path {path} not allowed for source {sid}; skipping")
                        continue
                except Exception:
                    print(f"Failed to validate allowed_paths for {sid}; skipping")
                    continue

            # pick rate limit from approval metadata if available
            rl = approval.get("rate_limit")
            try:
                rate_limit_seconds = float(rl) if rl is not None else 0
            except Exception:
                rate_limit_seconds = 0

            try:
                scr = cls(rate_limit_seconds=rate_limit_seconds, respect_robots=False)
                item = scr.scrape(s.get("url"), s.get("selectors", {}))
                integrate_scraped_item(item, sid)
            except Exception as e:  # pragma: no cover - runtime integration
                print(f"Error scraping {sid}: {e}")
    except Exception:
        print("scrape_all_impl: dependencies not available; skipping")


def _generate_agenda_impl() -> None:
    try:  # pragma: no cover - integration glue
        from agents.skills.president import generate_agenda_with_llm
        from ingest.storage import store_conversion
        from datetime import date

        notes = {"title": "Scheduled Agenda", "date": str(date.today()), "summary": "Auto-generated agenda."}
        md = generate_agenda_with_llm(notes)
        store_conversion(md, {"source": "scheduler"}, {}, "agenda_scheduled", "out")
    except Exception:
        print("generate_agenda_impl: dependencies not available; skipping")


# mapping of known persisted job names to functions
_KNOWN_JOB_FACTORIES: Dict[str, Callable[[], None]] = {
    "scrape_all_sources": _scrape_all_impl,
    "generate_weekly_agenda": _generate_agenda_impl,
}


def stop() -> None:
    """Stop the scheduler background thread and wait for it to finish."""
    global _runner_thread, _stop_event, _apscheduler
    if _apscheduler is not None:
        try:
            _apscheduler.shutdown(wait=False)
        except Exception:
            pass
        _apscheduler = None
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
            from ingest.scrapers import approvals as approvals_mod

            for s in sources:
                parser = s.get("parser")
                cls = parser_map.get(parser)
                if not cls:
                    print(f"No parser for {parser} (source {s.get('id')})")
                    continue

                sid = s.get("id")
                approval = approvals_mod.get_approval(sid)
                if not approval:
                    print(f"Skipping unapproved source {sid}")
                    continue

                # enforce allowed_paths
                allowed_paths = approval.get("allowed_paths")
                if allowed_paths:
                    try:
                        parsed = urllib.parse.urlparse(s.get("url") or "")
                        path = parsed.path or "/"
                        if isinstance(allowed_paths, str):
                            allowed_list = [allowed_paths]
                        else:
                            allowed_list = list(allowed_paths)
                        if not any(path.startswith(ap) for ap in allowed_list):
                            print(f"URL path {path} not allowed for source {sid}; skipping")
                            continue
                    except Exception:
                        print(f"Failed to validate allowed_paths for {sid}; skipping")
                        continue

                # rate limit from approval
                rl = approval.get("rate_limit")
                try:
                    rate_limit_seconds = float(rl) if rl is not None else 0
                except Exception:
                    rate_limit_seconds = 0

                try:
                    scr = cls(rate_limit_seconds=rate_limit_seconds, respect_robots=False)
                    item = scr.scrape(s.get("url"), s.get("selectors", {}))
                    integrate_scraped_item(item, sid)
                except Exception as e:  # pragma: no cover - runtime integration
                    print(f"Error scraping {sid}: {e}")

        def _generate_agenda() -> None:
            notes = {"title": "Scheduled Agenda", "date": str(date.today()), "summary": "Auto-generated agenda."}
            md = generate_agenda_with_llm(notes)
            store_conversion(md, {"source": "scheduler"}, {}, "agenda_scheduled", "out")

        register_job("scrape_all_sources", _scrape_all, interval_seconds=60 * 60 * 24)
        register_job("generate_weekly_agenda", _generate_agenda, interval_seconds=60 * 60 * 24 * 7)
    except Exception:  # pragma: no cover - best-effort registration
        # If dependencies aren't available (tests, import-time), skip registration
        print("Skipping default job registration (dependencies missing)")
