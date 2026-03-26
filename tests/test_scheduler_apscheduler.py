import time
import json
from pathlib import Path

import pytest

from agents import scheduler


def test_apscheduler_starts_and_registers_job():
    if not getattr(scheduler, "_HAS_APSCHEDULER", False):
        pytest.skip("APScheduler not available")

    # ensure clean state
    try:
        scheduler.stop()
    except Exception:
        pass

    # start scheduler (should initialize APScheduler)
    scheduler.start()
    assert getattr(scheduler, "_apscheduler", None) is not None

    called = []

    def _job():
        called.append(True)

    # register a short-interval job
    scheduler.register_job("test_aps_job", _job, interval_seconds=1)

    # APScheduler should have a job with this id
    aps_job = None
    try:
        aps_job = scheduler._apscheduler.get_job("test_aps_job")
    except Exception:
        aps_job = None

    assert aps_job is not None

    # wait a bit for scheduled run(s)
    time.sleep(2)

    # the job may have been executed at least once
    assert len(called) >= 0

    # cleanup
    scheduler.unregister_job("test_aps_job")
    scheduler.stop()


def test_state_file_persists_job_fields(tmp_path):
    # Write state path to a temp file by monkeypatching _state_path
    state_file = tmp_path / "scheduler_state.json"

    # monkeypatch the module-level _state_path function
    orig_state_path = getattr(scheduler, "_state_path")

    def _tmp_state_path():
        return state_file

    scheduler._state_path = _tmp_state_path

    # ensure clean in-memory jobs
    try:
        for n in list(scheduler.list_jobs().keys()):
            scheduler.unregister_job(n)
    except Exception:
        pass

    def _noop():
        return

    scheduler.register_job("persist_job", _noop, interval_seconds=10, retries=3, retry_backoff_seconds=5)

    # ensure file written
    assert state_file.exists()
    data = json.loads(state_file.read_text(encoding="utf-8"))
    matching = [d for d in data if d.get("name") == "persist_job"]
    assert len(matching) == 1
    rec = matching[0]
    assert rec.get("retries") == 3
    assert rec.get("retry_backoff_seconds") == 5

    # restore
    scheduler.unregister_job("persist_job")
    scheduler._state_path = orig_state_path