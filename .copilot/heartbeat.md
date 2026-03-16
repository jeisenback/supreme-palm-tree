## Heartbeat: agent liveness and periodic behavior

Purpose: document expectations for periodic checks, scheduled tasks, and
heartbeat messages that agents should emit when running long-lived processes
or when used as a scheduler worker.

Guidelines
- Emit a short heartbeat log every configured interval (e.g., 60s) containing:
  - uptime, memory usage (approx), and any pending job counts.
  - a short health status: `ok`, `degraded`, or `error`.
- Heartbeats should be extremely terse and machine-parseable (JSON lines
  are preferred).

Failure Modes
- On `degraded` or `error`, include an actionable hint and surface
  the last exception trace (truncated) to logs only; do not include full
  secrets or user data.

Operational Commands
- `status` — return a one-line summary of health and queued tasks.
- `metrics` — expose Prometheus-compatible counters when configured.
