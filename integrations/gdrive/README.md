Google Drive integration (PoC)
=================================

This folder contains a minimal scaffold for integrating with Google Drive.

Next steps to implement a working integration:

- Obtain OAuth 2.0 credentials (service account or OAuth client) and store
  them securely; update your environment or provide a path to `credentials_json`.
- Install `google-api-python-client` and `google-auth`.
- Implement `upload_file` to perform an authenticated upload into `folder_id`.

Human step required: add credentials and approve Drive access.
