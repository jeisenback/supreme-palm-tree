"""Example runner for the APScheduler-backed ProductionScheduler (PoC).

Usage:
  python scripts/run_scheduler_prod.py --jobstore-url sqlite:///./scheduler_jobs.sqlite

The script will register example jobs (if available) and start the scheduler.
"""
from __future__ import annotations

import os
import argparse
import time


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ProductionScheduler example")
    parser.add_argument("--jobstore-url", default=os.environ.get("SCHEDULER_JOBSTORE", "sqlite:///./scheduler_jobs.sqlite"))
    parser.add_argument("--once", action="store_true", help="Run jobs once and exit (synchronous)")
    args = parser.parse_args()

    try:
        from agents.scheduler_prod import ProductionScheduler
    except Exception as exc:
        print("ProductionScheduler unavailable: ", exc)
        print("Install 'apscheduler' to use this runner.")
        return

    sched = ProductionScheduler(jobstore_url=args.jobstore_url)

    # Try to register the project's default PoC jobs if available in agents.scheduler
    registered = False
    try:
        from agents.scheduler import _scrape_all_impl, _generate_agenda_impl

        sched.register_job("scrape_all_sources", _scrape_all_impl, interval_seconds=60 * 60 * 24)
        sched.register_job("generate_weekly_agenda", _generate_agenda_impl, interval_seconds=60 * 60 * 24 * 7)
        registered = True
    except Exception:
        # fall back to a simple heartbeat job
        def _heartbeat():
            print(f"heartbeat: {time.asctime()}")

        sched.register_job("heartbeat", _heartbeat, interval_seconds=60)

    if args.once:
        print("Running jobs once (synchronously)")
        if registered:
            try:
                _scrape_all_impl()
            except Exception:
                pass
            try:
                _generate_agenda_impl()
            except Exception:
                pass
        else:
            _heartbeat()
        return

    print("Starting production scheduler. Press Ctrl-C to exit.")
    sched.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping scheduler...")
        sched.stop()


if __name__ == "__main__":
    main()
