# Google Drive Integration

This document explains how to configure and use the Google Drive integration
in this repo. The code provides both service-account and OAuth flows and
includes tools for uploading files, listing and downloading files, and a
Drive-based watcher that can download new files and trigger local processing.

Important files

- `integrations/gdrive/drive_client.py` — Drive helper with `DriveClient.upload_file`, `list_files`, and `download_file`.
- `agents/watcher.py` — `start_drive_watcher()` polls a Drive folder, downloads new files, and invokes a callback. Persistent seen-state is stored at `out/drive_seen.json` by default.
- `agents/agents_cli.py` — CLI commands:
  - `agents-cli watch-drive --folder-id <FOLDER_ID> --credentials /path/creds.json`
  - `agents-cli weekly-update publish <id> --drive-folder <FOLDER_ID> --credentials /path/creds.json`

Authentication options

1) Service account (recommended for server-to-server uploads)

- Create a service account in Google Cloud IAM with the Drive API scope and grant it access to the target Drive folder (share folder with the service account email).
- Download the JSON key file and provide its path to the CLI or `DriveClient` via `--credentials /path/to/key.json`.

Example (upload a published weekly update):

```bash
agents-cli weekly-update publish <draft-id> --drive-folder 1AbCdEfGh --credentials /secrets/drive-sa.json
```

2) OAuth user flow (interactive, for desktop or single-user app)

- Use `integrations/gdrive/oauth.py` helper (if present) to run the OAuth flow and obtain tokens.
- Provide `--credentials client_secrets.json --oauth-token /path/to/token.json --credential-type oauth` to the CLI.

Drive watcher

Start a Drive watcher that polls a folder and processes new files (downloads to a temporary dir and calls the configured callback):

```bash
agents-cli watch-drive --folder-id 1AbCdEfGh --credentials /secrets/drive-sa.json --state-path out/drive_seen.json
```

- `--state-path` overrides the default persistence path (default: `out/drive_seen.json`). This file stores metadata for seen files and prevents re-downloading the same file after restarts.
- The watcher uses polling by default and keeps an in-memory set of seen ids; the persisted state enables skipping files across restarts.

Examples

Use the example script `scripts/drive_examples.py` to experiment with listing, downloading and uploading files. It demonstrates how to instantiate `DriveClient` and call the common APIs.

Testing and local development

- The repo includes unit tests that mock `DriveClient` so CI does not need real credentials.
- For end-to-end testing you'll need valid credentials and a Drive folder id.

Security

- Keep service-account JSON files and OAuth tokens out of the repo. Use secure storage (secrets manager) or mount them at runtime.
- The CLI options accept a path to credentials; avoid passing secrets on shared command history.

Next steps / production suggestions

- Consider using Drive push notifications (webhooks) for real-time detection instead of polling.
- Replace the JSON persistence with SQLite or a small DB if you require stronger consistency or concurrent access.
- Use a dedicated service account with least privilege to the folder(s) the application needs.
