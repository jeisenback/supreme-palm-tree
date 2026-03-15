"""Production-ready scheduler backend using APScheduler (PoC).

This module provides a `ProductionScheduler` class that uses APScheduler's
BackgroundScheduler and optional SQLAlchemyJobStore (if SQLAlchemy is
available) for persistence. Imports are guarded so that the rest of the
project and tests can run without APScheduler installed.

Usage (optional):

    from agents.scheduler_prod import ProductionScheduler
    sched = ProductionScheduler(jobstore_url="sqlite:///./scheduler_jobs.sqlite")
    sched.register_job("name", func, interval_seconds=60)
    sched.start()

If APScheduler is not installed, attempting to instantiate `ProductionScheduler`
will raise `RuntimeError` with instructions to install `apscheduler`.
"""
from __future__ import annotations

from typing import Callable, Dict, Any
import time
import traceback

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.executors.pool import ThreadPoolExecutor
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    APS_AVAILABLE = True
except Exception:  # pragma: no cover - guards when package not present
    BackgroundScheduler = None  # type: ignore
    ThreadPoolExecutor = None  # type: ignore
    SQLAlchemyJobStore = None  # type: ignore
    APS_AVAILABLE = False


class ProductionScheduler:
    """APScheduler-backed scheduler with optional jobstore and simple retries.

    This is a PoC: it supports interval jobs and basic retry semantics.
    """

    def __init__(self, jobstore_url: str | None = None, max_workers: int = 10):
        if not APS_AVAILABLE:
            raise RuntimeError("APScheduler is not installed. Install 'apscheduler' to use ProductionScheduler.")

        executors = {"default": ThreadPoolExecutor(max_workers)}
        jobstores = {}
        if jobstore_url and SQLAlchemyJobStore is not None:
            jobstores["default"] = SQLAlchemyJobStore(url=jobstore_url)

        self._sched = BackgroundScheduler(executors=executors, jobstores=jobstores)
        self._started = False

    def _wrap_with_retries(self, func: Callable[[], None], retries: int = 2, backoff_seconds: float = 1.0):
        def _runner():
            attempt = 0
            while True:
                try:
                    func()
                    return
                except Exception as exc:  # pragma: no cover - cannot simulate here
                    attempt += 1
                    print(f"Job failed (attempt {attempt}): {exc}")
                    traceback.print_exc()
                    if attempt > retries:
                        print("Max retries reached; giving up")
                        return
                    time.sleep(backoff_seconds * (2 ** (attempt - 1)))
        return _runner

    def register_job(self, name: str, func: Callable[[], None], interval_seconds: int, retries: int = 2) -> None:
        wrapped = self._wrap_with_retries(func, retries=retries)
        # remove existing job if present
        try:
            if self._sched.get_job(job_id=name):
                self._sched.remove_job(job_id=name)
        except Exception:
            pass
        self._sched.add_job(wrapped, "interval", seconds=interval_seconds, id=name, replace_existing=True)

    def unregister_job(self, name: str) -> None:
        try:
            self._sched.remove_job(job_id=name)
        except Exception:
            pass

    def list_jobs(self) -> Dict[str, Any]:
        jobs = {}
        try:
            for j in self._sched.get_jobs():
                jobs[j.id] = {"next_run_time": str(j.next_run_time), "trigger": str(j.trigger)}
        except Exception:
            pass
        return jobs

    def start(self) -> None:
        if not self._started:
            self._sched.start()
            self._started = True

    def stop(self, wait: bool = True) -> None:
        if self._started:
            self._sched.shutdown(wait=wait)
            self._started = False

    def run_once(self) -> None:
        # Run all scheduled jobs once synchronously by invoking their functions
        for j in list(self._sched.get_jobs()):
            try:
                jobfunc = j.func
                # APS stores pickled callables; calling run directly isn't trivial.
                # For PoC, schedule a one-off immediate execution using add_job and remove it.
                self._sched.add_job(jobfunc, "date", run_date=None)
            except Exception:
                pass
