import time

from agents import scheduler


def test_register_and_run_once():
    called = []

    def _job():
        called.append("ok")

    scheduler.register_job("test_job", _job, interval_seconds=1)
    # run_once should synchronously execute registered jobs
    scheduler.run_once()
    assert called == ["ok"]


def test_list_jobs_contains_registered():
    # ensure list_jobs reflects registration
    scheduler.register_job("xx", lambda: None, interval_seconds=5)
    lj = scheduler.list_jobs()
    assert "xx" in lj
