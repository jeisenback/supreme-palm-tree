Scheduler — running the project's scheduler under system services
===============================================================

This file provides example configurations for running the project's scheduler
either as a systemd service (Linux) or as a Windows Scheduled Task. The
scheduler is intentionally lightweight and suitable for demos; for production
use consider APScheduler, Celery, or external job platforms.

Files used by examples
- `scripts/run_scheduler.py` — small runner that registers default jobs and
  starts the scheduler loop (or runs jobs once with `--once`).

Systemd example
---------------

1. Create a system user (optional):

   sudo useradd --system --no-create-home nonprofit

2. Create a systemd service file `/etc/systemd/system/nonprofit-scheduler.service`:

```
[Unit]
Description=Nonprofit Tool Scheduler
After=network.target

[Service]
Type=simple
User=nonprofit
WorkingDirectory=/path/to/your/repo
Environment=PYTHONPATH=/path/to/your/repo
ExecStart=/path/to/venv/bin/python scripts/run_scheduler.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

3. Reload systemd and enable the service:

```
sudo systemctl daemon-reload
sudo systemctl enable --now nonprofit-scheduler.service
sudo journalctl -u nonprofit-scheduler.service -f
```

Windows Scheduled Task example (PowerShell)
------------------------------------------

1. Open an elevated PowerShell prompt and create a scheduled task that runs
   the scheduler at startup and keeps it running.

2. Example using `Register-ScheduledTask` with an Action that starts Python
   in a virtual environment and runs the `scripts/run_scheduler.py` script:

```powershell
$action = New-ScheduledTaskAction -Execute 'C:\path\to\venv\Scripts\python.exe' -Argument 'C:\path\to\repo\scripts\run_scheduler.py'
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -RunLevel Highest
Register-ScheduledTask -TaskName "NonprofitToolScheduler" -Action $action -Trigger $trigger -Principal $principal

# To start immediately:
Start-ScheduledTask -TaskName "NonprofitToolScheduler"
# To view logs: use Event Viewer -> Applications and Services Logs, or
# capture stdout/stderr to a file by wrapping the command in a launcher script.
```

Notes and recommendations
-------------------------
- When running under a system scheduler, prefer absolute paths for `WorkingDirectory`
  and the Python executable.
- Keep secrets and credentials out of the repository; use OS-level secret stores
  or environment variables provided by the host.
- For long-running or production workloads, replace the in-process scheduler
  with a more robust job runner and add monitoring/alerting.

APScheduler + SQLAlchemy jobstore (optional)
------------------------------------------
- To persist scheduled jobs across restarts, the project includes an optional
  APScheduler-backed production scheduler at `agents/scheduler_prod.py`.
- Install the dependencies in `requirements.txt` (APScheduler + SQLAlchemy).
- Example usage with a SQLite jobstore:

```bash
python -c "from agents.scheduler_prod import ProductionScheduler; sched = ProductionScheduler(jobstore_url='sqlite:///./scheduler_jobs.sqlite'); sched.start();"
```

- For a production-grade database, provide a PostgreSQL or MySQL URL and ensure
  the database is backed up and secured. See APScheduler docs for migration notes.
