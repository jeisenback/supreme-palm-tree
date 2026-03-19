import json
import sqlite3
from pathlib import Path

import pytest

from agents import scheduler


def test_apscheduler_persistence_restart(tmp_path):
    # only run when APScheduler is available in CI/dev env
    if not getattr(scheduler, "_HAS_APSCHEDULER", False):
        pytest.skip("APScheduler not available")

    # point state + db to temp paths
    state_fp = tmp_path / "sch.json"
    db_fp = tmp_path / "jobs.db"
    orig_state = scheduler._state_path
    orig_db = scheduler._db_path
    scheduler._state_path = lambda: state_fp
    scheduler._db_path = lambda: db_fp

    # ensure clean
    try:
        scheduler.stop()
    except Exception:
        pass
    scheduler._JOBS.clear()

    called = {"n": 0}

    def flaky():
        called["n"] += 1
        if called["n"] == 1:
            raise RuntimeError("transient")

    # register and run once to cause a failure and persist runtime state
    scheduler.register_job("int-flaky", flaky, interval_seconds=10, retries=2, retry_backoff_seconds=1)
    job = scheduler._JOBS.get("int-flaky")
    assert job is not None

    try:
        scheduler._run_job_safe(job)
    except Exception:
        pass

    # DB should contain persisted runtime state
    assert db_fp.exists()
    conn = sqlite3.connect(str(db_fp))
    cur = conn.cursor()
    cur.execute("SELECT retry_attempts FROM job_state WHERE name = ?", ("int-flaky",))
    rows = cur.fetchall()
    conn.close()
    assert rows and rows[0][0] >= 1

    # simulate restart: clear in-memory jobs and let loader restore
    scheduler._JOBS.clear()
    # register factory for loader
    scheduler._KNOWN_JOB_FACTORIES["int-flaky"] = flaky
    try:
        scheduler._load_state()
        job2 = scheduler._JOBS.get("int-flaky")
        assert job2 is not None
        assert job2.retry_attempts >= 1
    finally:
        scheduler._KNOWN_JOB_FACTORIES.pop("int-flaky", None)
        # restore module-level helpers
        scheduler._state_path = orig_state
        scheduler._db_path = orig_db
        try:
            scheduler.unregister_job("int-flaky")
        except Exception:
            pass
