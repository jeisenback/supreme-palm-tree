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

## Deployment (Render)

- Blueprint file: `render.yaml`
- Start command: `streamlit run apps/facilitator_ui.py --server.port $PORT --server.address 0.0.0.0`
- Configure `FACILITATOR_PASSWORD` and optional OAuth/LLM env vars in Render.
- For persistent runtime files on Render, mount a disk and set `FACILITATOR_DATA_DIR` to the mount path.

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

