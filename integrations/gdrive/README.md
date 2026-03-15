Google Drive integration (PoC)
=================================

This folder contains a minimal scaffold for integrating with Google Drive.

Next steps to implement a working integration:

- Obtain OAuth 2.0 credentials (service account or OAuth client) and store
  them securely; update your environment or provide a path to `credentials_json`.
- Install `google-api-python-client` and `google-auth`.
- Implement `upload_file` to perform an authenticated upload into `folder_id`.

Human step required: add credentials and approve Drive access.

Quickstart (service account)
1. Create a Google Cloud service account with `Drive API` enabled and download the JSON key file.
2. Provide the path to the key file when constructing `DriveClient`, e.g.: 

```py
from integrations.gdrive.drive_client import DriveClient
client = DriveClient(credentials_json='/path/to/sa.json', folder_id='DRIVE_FOLDER_ID')
client.upload_file('out/agenda.md', mime_type='text/markdown')
```

Quickstart (OAuth user flow)
1. Create OAuth 2.0 client credentials in Google Cloud Console and download `client_secrets.json`.
2. Run the included helper to obtain a token (opens a local browser):

```py
from integrations.gdrive.oauth import run_local_oauth_flow
creds = run_local_oauth_flow('client_secrets.json', token_path='token.json')
```

3. Use the token file with `DriveClient`:

```py
from integrations.gdrive.drive_client import DriveClient
client = DriveClient(credentials_json='client_secrets.json', credential_type='oauth', oauth_token_path='token.json', folder_id='DRIVE_FOLDER_ID')
client.upload_file('out/agenda.md')
```

Notes
- The repository tests mock Google libraries; installing real deps is required to run against the real Drive API.
- Store service account keys and OAuth tokens securely and do not commit them.
