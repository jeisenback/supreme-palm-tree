import sys
import types
import time
from pathlib import Path


def test_drive_watcher_redownloads_on_modifiedtime_change(tmp_path: Path):
    # Prepare a fake DriveClient module where file's modifiedTime changes
    mod_name = "integrations.gdrive.drive_client"
    fake_mod = types.ModuleType(mod_name)

    class FakeDriveClient:
        def __init__(self, credentials_json=None, folder_id=None, credential_type=None, oauth_token_path=None):
            self._calls = 0

        def list_files(self, folder_id=None):
            # First call returns modifiedTime T1, subsequent calls T2
            self._calls += 1
            if self._calls == 1:
                return [{"id": "FX", "name": "meet.txt", "modifiedTime": "2026-03-01T00:00:00Z"}]
            return [{"id": "FX", "name": "meet.txt", "modifiedTime": "2026-03-02T00:00:00Z"}]

        def download_file(self, file_id, dest_path):
            # write a file so callback can process
            Path(dest_path).write_text("Action: Do stuff\n")

    fake_mod.DriveClient = FakeDriveClient
    sys.modules[mod_name] = fake_mod

    from agents.watcher import start_drive_watcher

    state_path = tmp_path / "seen.json"
    calls = []

    def cb(pth: str):
        calls.append(pth)

    # start watcher: first poll should download (T1)
    th = start_drive_watcher("folder-x", cb, poll_interval=0.2, background=True, state_path=str(state_path))
    time.sleep(0.6)
    assert len(calls) >= 1

    # simulate restart: start a new watcher pointing to same state_path
    calls2 = []

    def cb2(pth: str):
        calls2.append(pth)

    th2 = start_drive_watcher("folder-x", cb2, poll_interval=0.2, background=True, state_path=str(state_path))
    time.sleep(0.6)
    # Because modifiedTime changed in fake client, second watcher should have downloaded again
    assert len(calls2) >= 1

    del sys.modules[mod_name]
