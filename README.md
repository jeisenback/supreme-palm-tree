# Nonprofit Tool

Nonprofit board operations and facilitator tooling for the IIBA East Tennessee workflow.

## What is in this repo

- **Facilitator UI** (`apps/facilitator_ui.py`): live session controls, published-only filter, Panel Mode, notes/actions, participant view.
- **Content Studio** (`apps/content_studio.py`): Gap Radar, content editor, AI first-draft generator.
- **Board Showcase** (`apps/board_showcase.py`): no-login program presentation with live learner outcomes metrics.
- **Learner Dashboard** (`apps/learner_dashboard.py`): attendance tracking, per-member progress, readiness score, heatmap.
- **Ingest pipeline**: convert and normalize source documents into Markdown/JSON context.
- **Role agents**: president/secretary/treasurer skills with LLM-safe fallbacks.
- **Scheduler and scraper integrations** for recurring operational workflows.

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

Run the board showcase (no login, board-facing):

```bash
streamlit run apps/board_showcase.py --server.port 8502
```

Run the content studio (authoring + gap radar):

```bash
streamlit run apps/content_studio.py --server.port 8503
```

Run the learner dashboard (attendance + readiness):

```bash
streamlit run apps/learner_dashboard.py --server.port 8504
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

## Deployment (Render)

- Blueprint file: `render.yaml`
- Two services are defined:
  - `ecba-facilitator` — facilitator UI (session controls, content authoring, OAuth)
  - `ecba-board-showcase` — board showcase (read-only, no env vars required)
- Health check path: `/_stcore/health`
- Configure `FACILITATOR_PASSWORD` and optional OAuth/LLM env vars in Render for the facilitator service.
- Free tier uses ephemeral storage. Runtime state in `etn/outputs` is reset on restart or redeploy.
- If you need persistent state, move to a paid Render plan and attach a disk.

Render deployment steps:

1. Push this repository to GitHub.
2. In Render, click **New + > Blueprint**.
3. Select the repository with this `render.yaml`.
4. Confirm services `ecba-facilitator` and `ecba-board-showcase` and create the blueprint.
5. In the facilitator service settings, set required secret values:
	- `FACILITATOR_PASSWORD`
	- `ANTHROPIC_API_KEY` (optional — enables AI draft generation)
	- `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` (optional — enables GitHub OAuth login)
6. Trigger a deploy and wait for health checks to pass.
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
- Curriculum platform design (Sprint 5): `docs/designs/curriculum-platform.md`
- Active/deferred backlog: `TODOS.md`
- Project task plan: `TASKS.md`
- Project state (current sprint, app inventory): `PROJECT_STATE.md`
- Facilitator UI guide: `apps/README_facilitator.md`
- Board showcase guide: `apps/README_board_showcase.md`
- Attendance data schema and PII notice: `data/attendance/README.md`

