import json
import time
from pathlib import Path

from agents import scheduler


def test_db_persists_retry_attempts(tmp_path):
    # ensure APScheduler is available for this test
    if not getattr(scheduler, "_HAS_APSCHEDULER", False):
        import pytest

        pytest.skip("APScheduler not available")

    # point DB to temp path by monkeypatching _db_path
    db_file = tmp_path / "jobs.db"
    orig_db_path = scheduler._db_path

    scheduler._db_path = lambda: db_file

    # clean any in-memory jobs
    try:
        for n in list(scheduler.list_jobs().keys()):
            scheduler.unregister_job(n)
    except Exception:
        pass

    state = {"called": 0}

    def flaky():
        state["called"] += 1
        if state["called"] == 1:
            raise RuntimeError("fail once")
        return

    scheduler.register_job("db-flaky", flaky, interval_seconds=10, retries=2, retry_backoff_seconds=1)
    job = scheduler._JOBS.get("db-flaky")
    assert job is not None

    # run to cause failure and increment retry_attempts
    try:
        scheduler._run_job_safe(job)
    except Exception:
        pass

    # DB should exist and contain row
    assert db_file.exists()
    # read db directly
    import sqlite3

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT name, last_run, retry_attempts FROM job_state WHERE name = ?", ("db-flaky",))
    rows = cur.fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][2] >= 1

    # cleanup
    scheduler.unregister_job("db-flaky")
    scheduler._db_path = orig_db_path