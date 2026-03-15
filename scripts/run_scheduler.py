"""Run the in-process scheduler for demos or system scheduling.

Usage examples:
  - Run once (execute registered jobs synchronously):
      PYTHONPATH=. python scripts/run_scheduler.py --once

  - Start background scheduler (runs until interrupted):
      PYTHONPATH=. python scripts/run_scheduler.py

This script registers the default PoC jobs (if available) and starts the
scheduler. It is intentionally minimal so it can be invoked by system schedulers
or used locally for testing.
"""
from __future__ import annotations

import argparse
import time

from agents import scheduler


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the project's scheduler")
    parser.add_argument("--once", action="store_true", help="Run each job once and exit")
    args = parser.parse_args()

    # register PoC jobs if available
    scheduler.register_default_jobs()

    if args.once:
        scheduler.run_once()
        return 0

    try:
        scheduler.start()
        print("Scheduler started. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping scheduler...")
        scheduler.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
