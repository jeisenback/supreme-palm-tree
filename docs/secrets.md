Secrets & Configuration
=======================

This project reads configuration from environment variables. For local development
it's convenient to use a `.env` file (never commit `.env` to the repo). The
project provides the following guidance and an example file `.env.example`.

Recommended env vars
- `ANTHROPIC_API_KEY` — (optional) Anthropic API key for LLM usage.
- `ANTHROPIC_MODEL` — model name (optional).
- `GDRIVE_CREDENTIAL_TYPE` — `service_account` or `oauth`.
- `GDRIVE_CREDENTIALS` — base64 or path to credentials for Drive (keep secret).
- `GDRIVE_FOLDER_ID` — destination folder ID for uploads.
- `SCHEDULER_JOBSTORE` — optional SQLAlchemy jobstore URL, e.g. `sqlite:///./scheduler_jobs.sqlite`.
- `SCHEDULER_METRICS_PORT` — optional Prometheus metrics port for the scheduler.

Local development
- Create a `.env` file from `.env.example` and fill in values for local testing.
- Use `python-dotenv` to load `.env` (the repo includes a small helper `agents/secrets.py`).

CI / Production
- Do NOT store secrets in the repo. Use your platform's secrets store (GitHub Actions Secrets,
  cloud provider secret manager, or HashiCorp Vault).
- Ensure service account keys have the minimal required permissions.

Security notes
- Rotate credentials on compromise and remove unused credentials.
- Restrict Drive access to a dedicated service account for uploads.
- Consider auditing access via Cloud Audit Logs or equivalent.

Example `.env.example` file is included in the repository.
