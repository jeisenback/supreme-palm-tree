import json
import time
from pathlib import Path

from agents import scheduler


def test_retry_attempts_persist_across_reload(tmp_path):
    # Use temp state file
    state_fp = tmp_path / "sch.json"
    orig_state = scheduler._state_path

    scheduler._state_path = lambda: state_fp

    # ensure clean
    try:
        for n in list(scheduler.list_jobs().keys()):
            scheduler.unregister_job(n)
    except Exception:
        pass

    # define a job that will fail once (raise) then succeed
    state = {"called": 0}

    def flaky():
        state["called"] += 1
        if state["called"] == 1:
            raise RuntimeError("fail once")
        return

    # register job with 2 retries
    scheduler.register_job("flaky-job", flaky, interval_seconds=10, retries=2, retry_backoff_seconds=1)

    # invoke job runner directly to simulate execution and failure
    job = scheduler._JOBS.get("flaky-job")
    assert job is not None

    # run once -> should increment retry_attempts and persist
    try:
        scheduler._run_job_safe(job)
    except Exception:
        pass

    # ensure persisted file contains retry_attempts > 0
    assert state_fp.exists()
    data = json.loads(state_fp.read_text(encoding="utf-8"))
    recs = [d for d in data if d.get("name") == "flaky-job"]
    assert len(recs) == 1
    assert recs[0].get("retry_attempts", 0) >= 1

    # simulate reload by clearing in-memory jobs and loading state
    scheduler._JOBS.clear()
    # register factory so loader can recreate the job
    scheduler._KNOWN_JOB_FACTORIES["flaky-job"] = flaky
    try:
        scheduler._load_state()
    finally:
        # remove factory to avoid side-effects
        scheduler._KNOWN_JOB_FACTORIES.pop("flaky-job", None)

    job2 = scheduler._JOBS.get("flaky-job")
    assert job2 is not None
    # retry_attempts should be restored
    assert job2.retry_attempts >= 1

    # cleanup
    scheduler.unregister_job("flaky-job")
    scheduler._state_path = orig_state