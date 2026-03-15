import sys
import types
import time
from pathlib import Path


def test_drive_watcher_persists_and_skips_on_restart(tmp_path: Path):
    # Prepare a fake DriveClient module
    mod_name = "integrations.gdrive.drive_client"
    fake_mod = types.ModuleType(mod_name)

    class FakeDriveClient:
        def __init__(self, credentials_json=None, folder_id=None, credential_type=None, oauth_token_path=None):
            self.folder_id = folder_id
            # one file available
            self._files = [{"id": "F1", "name": "meeting1.txt", "modifiedTime": "2026-03-01T00:00:00Z"}]

        def list_files(self, folder_id=None):
            return self._files

        def download_file(self, file_id, dest_path):
            Path(dest_path).write_text("Action: Follow up on X\n")

    fake_mod.DriveClient = FakeDriveClient
    sys.modules[mod_name] = fake_mod

    from agents.watcher import start_drive_watcher

    state_path = tmp_path / "seen.json"
    calls = []

    def cb(pth: str):
        calls.append(pth)

    # start watcher (daemon) which should download the file and persist seen id
    th = start_drive_watcher("folder-x", cb, poll_interval=0.2, background=True, credentials_json=None, credential_type="service_account", oauth_token_path=None, state_path=str(state_path))
    time.sleep(0.6)
    assert state_path.exists()
    data = state_path.read_text()
    assert "F1" in data
    assert len(calls) >= 1

    # start a new watcher (simulating restart) with a DriveClient that would error if re-downloaded
    calls2 = []

    class FakeDriveClient2(FakeDriveClient):
        def download_file(self, file_id, dest_path):
            # mark if called again
            calls2.append(file_id)

    fake_mod.DriveClient = FakeDriveClient2
    sys.modules[mod_name] = fake_mod

    th2 = start_drive_watcher("folder-x", cb, poll_interval=0.2, background=True, credentials_json=None, credential_type="service_account", oauth_token_path=None, state_path=str(state_path))
    time.sleep(0.6)
    # no new downloads should have happened because file id already persisted
    assert calls2 == []

    # cleanup
    del sys.modules[mod_name]
