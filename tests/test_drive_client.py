import sys
import types
import os
import pytest

from integrations.gdrive.drive_client import DriveClient


def test_upload_missing_packages_raises(monkeypatch, tmp_path):
    # Ensure google packages are not present
    monkeypatch.setitem(sys.modules, 'google', None)
    c = DriveClient(credentials_json=str(tmp_path/'creds.json'))
    with pytest.raises(RuntimeError):
        c.upload_file(str(tmp_path/'file.txt'))


def test_upload_calls_api(monkeypatch, tmp_path):
    # Create a fake credentials file
    creds_file = tmp_path / 'sa.json'
    creds_file.write_text('{}')
    # Create a dummy file to upload
    f = tmp_path / 'doc.md'
    f.write_text('hello')

    # Build fake google modules
    # Create a fake google.oauth2.service_account module
    fake_service_account = types.ModuleType('google.oauth2.service_account')
    fake_service_account.Credentials = types.SimpleNamespace(
        from_service_account_file=lambda *a, **k: 'creds'
    )

    class FakeFiles:
        def create(self, body=None, media_body=None, fields=None):
            class Exec:
                def execute(self_inner):
                    return {'id': 'file123', 'name': body.get('name')}
            return Exec()

    class FakeService:
        def files(self):
            return FakeFiles()

    def fake_build(service_name, version, credentials=None, cache_discovery=None):
        assert service_name == 'drive'
        assert version == 'v3'
        assert credentials == 'creds'
        return FakeService()

    fake_googleapiclient = types.SimpleNamespace(discovery=types.SimpleNamespace(build=fake_build), http=types.SimpleNamespace(MediaFileUpload=lambda p, mimetype=None: object()))

    # Ensure parent modules exist so import paths resolve
    monkeypatch.setitem(sys.modules, 'google', types.ModuleType('google'))
    monkeypatch.setitem(sys.modules, 'google.oauth2', types.ModuleType('google.oauth2'))
    monkeypatch.setitem(sys.modules, 'google.oauth2.service_account', fake_service_account)

    fake_discovery = types.ModuleType('googleapiclient.discovery')
    fake_discovery.build = fake_build
    fake_http = types.ModuleType('googleapiclient.http')
    fake_http.MediaFileUpload = lambda *a, **k: object()
    monkeypatch.setitem(sys.modules, 'googleapiclient', types.ModuleType('googleapiclient'))
    monkeypatch.setitem(sys.modules, 'googleapiclient.discovery', fake_discovery)
    monkeypatch.setitem(sys.modules, 'googleapiclient.http', fake_http)

    client = DriveClient(credentials_json=str(creds_file), folder_id='FOLDER')
    out = client.upload_file(str(f), mime_type='text/markdown')
    assert out['id'] == 'file123'
    assert out['name'] == 'doc.md'
