import sys
import types
from pathlib import Path

from agents.weekly_update import create_draft, publish_update, list_pending


def test_publish_triggers_drive_upload(tmp_path: Path):
    # inject a fake integrations.gdrive.drive_client module with DriveClient
    mod_name = "integrations.gdrive.drive_client"
    fake_mod = types.ModuleType(mod_name)

    class FakeDriveClient:
        last_instance = None

        def __init__(self, credentials_json=None, folder_id=None, credential_type=None, oauth_token_path=None):
            type(self).last_instance = self
            self.credentials_json = credentials_json
            self.folder_id = folder_id
            self.credential_type = credential_type
            self.oauth_token_path = oauth_token_path
            self.upload_called = False

        def upload_file(self, path, mime_type=None):
            self.upload_called = True
            self.upload_args = {"path": path, "mime_type": mime_type}
            return {"id": "fake-file-id"}

    fake_mod.DriveClient = FakeDriveClient
    sys.modules[mod_name] = fake_mod

    # prepare notes and create a draft
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "n1.md").write_text("Note A")

    meta = create_draft(title="DriveTest", notes_dir=str(notes), use_llm=False)
    assert any(i.get("id") == meta["id"] for i in list_pending())

    # publish with drive args
    dest = publish_update(meta["id"], drive_folder="F123", credentials_json="/fake/creds.json", credential_type="service_account")
    assert dest is not None

    # ensure fake DriveClient was used and upload_file called
    inst = FakeDriveClient.last_instance
    assert inst is not None
    assert inst.upload_called is True
    assert inst.folder_id == "F123"

    # cleanup injected module
    del sys.modules[mod_name]
