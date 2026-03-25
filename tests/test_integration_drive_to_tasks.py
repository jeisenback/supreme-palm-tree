import sys
import types
import time
from pathlib import Path

from agents.tasks import list_tasks
from agents import scheduler


def test_integration_drive_to_tasks(tmp_path: Path):
    # Inject a fake DriveClient that provides one transcript file
    mod_name = "integrations.gdrive.drive_client"
    fake_mod = types.ModuleType(mod_name)

    class FakeDriveClient:
        def __init__(self, credentials_json=None, folder_id=None, credential_type=None, oauth_token_path=None):
            self._called = 0

        def list_files(self, folder_id=None):
            return [{"id": "INT1", "name": "meeting1.txt", "modifiedTime": "2026-03-01T00:00:00Z"}]

        def download_file(self, file_id, dest_path):
            # Write a simple transcript containing an action item
            Path(dest_path).write_text("Action: Bob to draft the report.\n")

    fake_mod.DriveClient = FakeDriveClient
    sys.modules[mod_name] = fake_mod

    from agents.watcher import start_drive_watcher
    from agents.transcript_processor import process_transcript_file

    state_path = tmp_path / "seen.json"
    out_dir = tmp_path / "out"

    # Ensure scheduler clean state
    for n in list(scheduler.list_jobs().keys()):
        scheduler.unregister_job(n)

    processed = []

    def cb(p: str):
        # process downloaded transcript into tasks
        pth = process_transcript_file(p, out_dir=str(out_dir), use_llm=False)
        processed.append(pth)

    # Start the drive watcher (short poll interval)
    th = start_drive_watcher("folder-x", cb, poll_interval=0.2, background=True, state_path=str(state_path))
    time.sleep(0.8)

    # Assert the file was processed
    assert processed, "No transcript was processed"

    # Assert a task was created from the action item
    tasks = list_tasks()
    assert any("Bob" in (t.get("description") or "") for t in tasks)

    # Assert a reminder job was scheduled
    jobs = scheduler.list_jobs()
    assert any(n.startswith("reminder-") for n in jobs.keys())

    # Cleanup
    del sys.modules[mod_name]
