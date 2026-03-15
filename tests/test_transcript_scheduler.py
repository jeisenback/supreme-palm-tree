from pathlib import Path
import time

from agents.transcript_processor import process_transcript_file
from agents.tasks import list_tasks
from agents import scheduler


def test_transcript_creates_tasks_and_schedules(tmp_path: Path):
    # create a fake transcript file
    t = tmp_path / "meeting.txt"
    t.write_text("Action: Alice to send minutes.\nResearch: Look into grants.")

    # ensure scheduler state is clean
    for n in list(scheduler.list_jobs().keys()):
        scheduler.unregister_job(n)

    out = process_transcript_file(str(t), out_dir=str(tmp_path / "out"), use_llm=False)
    # check processed file created
    assert out.exists()

    tasks = list_tasks()
    assert any("Alice" in (it.get("description") or "") for it in tasks)

    # Check a reminder job was registered (name starts with reminder-)
    jobs = scheduler.list_jobs()
    assert any(n.startswith("reminder-") for n in jobs.keys())
