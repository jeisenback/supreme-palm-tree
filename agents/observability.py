"""Simple observability helpers (optional Prometheus integration).

This module is guarded so the project works when `prometheus_client` is not
installed. It provides `init_metrics_server(port)`, `record_job_start(name)` and
`record_job_end(name, start_ts, success)` for use by the scheduler.
"""
from __future__ import annotations

import time
from typing import Optional

try:
    from prometheus_client import start_http_server, Counter, Histogram  # type: ignore
    _PROM_AVAILABLE = True
except Exception:
    _PROM_AVAILABLE = False

_job_counter: Optional[Counter] = None
_job_duration: Optional[Histogram] = None
_server_started = False


def init_metrics_server(port: int = 8000) -> None:
    global _server_started, _job_counter, _job_duration
    if not _PROM_AVAILABLE:
        return
    if _server_started:
        return
    start_http_server(port)
    _job_counter = Counter("scheduler_job_runs_total", "Total scheduler job runs", ["job", "success"])  # type: ignore
    _job_duration = Histogram("scheduler_job_duration_seconds", "Job duration seconds", ["job"])  # type: ignore
    _server_started = True


def record_job_start(job_name: str) -> float:
    # return a start timestamp usable later by record_job_end
    return time.time()


def record_job_end(job_name: str, start_ts: float, success: bool = True) -> None:
    if not _PROM_AVAILABLE:
        return
    try:
        duration = time.time() - start_ts
        if _job_duration is not None:
            _job_duration.labels(job=job_name).observe(duration)  # type: ignore
        if _job_counter is not None:
            _job_counter.labels(job=job_name, success=str(success)).inc()  # type: ignore
    except Exception:
        # best-effort: do not raise
        return
*** End Patch