import sys
import types
import tempfile
import os

import pytest

from integrations.gdrive.oauth import run_local_oauth_flow


def test_oauth_missing_deps(monkeypatch, tmp_path):
    # Simulate missing google_auth_oauthlib
    monkeypatch.delitem(sys.modules, 'google_auth_oauthlib', None)
    with pytest.raises(RuntimeError):
        run_local_oauth_flow(str(tmp_path/'client.json'))


def test_oauth_flow_runs_and_saves(monkeypatch, tmp_path):
    # Create fake InstalledAppFlow
    fake_flow_mod = types.ModuleType('google_auth_oauthlib.flow')

    class FakeFlow:
        @staticmethod
        def from_client_secrets_file(path, scopes=None):
            class F:
                def run_local_server(self, port=0):
                    class Creds:
                        def to_json(self):
                            return '{"token":"abc"}'

                    return Creds()

            return F()

    fake_flow_mod.InstalledAppFlow = FakeFlow

    # Ensure imports resolve
    monkeypatch.setitem(sys.modules, 'google_auth_oauthlib.flow', fake_flow_mod)
    # Provide google.auth.transport.requests.Request and google.auth
    google_mod = types.ModuleType('google')
    google_auth_mod = types.ModuleType('google.auth')
    transport_mod = types.ModuleType('google.auth.transport')
    requests_mod = types.ModuleType('google.auth.transport.requests')
    # add a dummy Request callable
    requests_mod.Request = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, 'google', google_mod)
    monkeypatch.setitem(sys.modules, 'google.auth', google_auth_mod)
    monkeypatch.setitem(sys.modules, 'google.auth.transport', transport_mod)
    monkeypatch.setitem(sys.modules, 'google.auth.transport.requests', requests_mod)
    # Run
    client_file = tmp_path / 'client.json'
    client_file.write_text('{}')
    token_path = tmp_path / 'token.json'
    creds = run_local_oauth_flow(str(client_file), token_path=str(token_path))
    assert hasattr(creds, 'to_json')
    assert token_path.exists()
