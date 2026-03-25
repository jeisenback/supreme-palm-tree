# Nonprofit Tool

Nonprofit board operations and facilitator tooling for the IIBA East Tennessee workflow.

## What is in this repo

- Facilitator web app (Streamlit): live session controls, attendance capture, notes/actions, content authoring, and participant view.
- Ingest pipeline: convert and normalize source documents into Markdown/JSON context.
- Role agents: president/secretary/treasurer skills with LLM-safe fallbacks.
- Scheduler and scraper integrations for recurring operational workflows.

## Quickstart

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Run the facilitator app locally:

```bash
streamlit run apps/facilitator_ui.py
```

Optional runtime state directory (defaults to `etn/outputs`):

```bash
export FACILITATOR_DATA_DIR=/path/to/state
```

## Testing

Local non-integration test run:

```bash
pytest -q -m "not integration"
```

Role agents
-----------

This repository includes PoC role agents to help board officers and staff. Invoke them via the `agents-cli` entrypoint:

Examples:

```bash
# Fundraising plan from inline CSV
PYTHONPATH=. python -m agents.agents_cli role fundraising --csv "donor,amount\nAlice,100\nBob,50\n"

# Membership insights from a file
PYTHONPATH=. python -m agents.agents_cli role membership --csv-file data/members.csv

# Draft communications from JSON
PYTHONPATH=. python -m agents.agents_cli role communications --json-file data/ctx.json

# Professional development plan
PYTHONPATH=. python -m agents.agents_cli role professional_development --json-file data/skills.json

# Operations checklist
PYTHONPATH=. python -m agents.agents_cli role operations --json-file data/ops.json

# Accelerator plan
PYTHONPATH=. python -m agents.agents_cli role accelerator --json-file data/apps.json
```

## Deployment (Render)

- Blueprint file: `render.yaml`
- Start command: `streamlit run apps/facilitator_ui.py --server.port $PORT --server.address 0.0.0.0`
- Health check path: `/_stcore/health`
- Configure `FACILITATOR_PASSWORD` and optional OAuth/LLM env vars in Render.
- Free tier uses ephemeral storage. Runtime state in `etn/outputs` is reset on restart or redeploy.
- If you need persistent state, move to a paid Render plan and attach a disk.

Render migration steps:

1. Push this repository and branch to GitHub.
2. In Render, click New + > Blueprint.
3. Select the repository and branch with this `render.yaml`.
4. Confirm service `ecba-facilitator` and create the blueprint.
5. In Render service settings, set required secret values:
	- `FACILITATOR_PASSWORD`
	- `ANTHROPIC_API_KEY` (optional)
	- `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` (optional)
6. Trigger a deploy and wait for the health check to pass.
7. Open the Render URL and validate login + content authoring flow.

If you later upgrade off free tier and want persistence:

1. Change the Render service plan to a disk-capable paid tier.
2. Add a Render Disk and mount it, for example at `/var/data`.
3. Set `FACILITATOR_DATA_DIR=/var/data`.

## Legacy ingest utilities

The repository still includes document conversion and generation helpers under `ingest/`.

- Convert DOCX to Markdown: `python ingest/docx_to_md.py <file.docx>`
- Generate from templates: `python ingest/generate_cli.py ...`

## Documentation index

- Product and architecture requirements: `REQUIREMENTS.md`
- UI design system: `DESIGN.md`
- Facilitator UI design notes: `DESIGN_UI.md`
- Sprint heartbeat: `HEARTBEAT.md`
- Active/deferred backlog: `TODOS.md`
- Project task plan: `TASKS.md`

