Facilitator UI (Streamlit) — Prototype

Run locally

1. Activate your virtualenv and install requirements:

```bash
source .venv/Scripts/activate
pip install -r requirements.txt
```

2. Start the prototype:

```bash
streamlit run apps/facilitator_ui.py
```

Notes
- The app reads `etn/outputs/iiba_events_parsed.csv` if present. If not found it shows sample data.
- Notes and actions are appended to `etn/outputs/facilitator_notes.csv`.

GitHub OAuth setup

1. Create a GitHub OAuth App: https://github.com/settings/developers
	- Application name: (your choice)
	- Homepage URL: `http://localhost:8501/` (for local testing)
	- Authorization callback URL: `http://localhost:8501/`

2. Set environment variables in your shell or deployment platform:

```bash
export GITHUB_CLIENT_ID=<your-client-id>
export GITHUB_CLIENT_SECRET=<your-client-secret>
export OAUTH_REDIRECT_URI=http://localhost:8501/
# optional fallback password for local login
export FACILITATOR_PASSWORD=<your-password>
```

3. Restart the app and use the "Sign in with GitHub" link in the sidebar. The app will exchange the code and persist a 7-day session in `etn/outputs/facilitator_session.json`.

Quick start scripts

You can use the provided helper scripts to run the app locally:

- Unix / Git Bash / WSL:

```bash
./scripts/start_facilitator.sh
```

- Windows (cmd.exe):

```
scripts\start_facilitator.bat
```


Deploy to Render (quick)

1. Commit and push this repository to GitHub.
2. Create a new Web Service on Render and connect your GitHub repo.
3. Use the following build and start commands (Render will set `$PORT`):

- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run apps/facilitator_ui.py --server.port $PORT --server.address 0.0.0.0`

4. Set an environment variable `STREAMLIT_SERVER_HEADLESS=true` in the Render dashboard to avoid opening a browser on the server.

If you need a managed backend or secure auth, consider a small FastAPI app and host the API on Render, with this frontend calling the API.
