# IIBA East TN — Board Agents Platform

AI-assisted board operations platform for the IIBA East Tennessee Chapter, including an ECBA certification study program facilitator, a board showcase app, role agents for board officers, and an automated ingest/scheduler pipeline.

## Apps

### Board Showcase (`apps/board_showcase.py`)
Clean no-login Streamlit app presenting the ECBA study program to board members and prospective participants. No setup required for viewers — just share the URL.

```bash
bash scripts/start_board_showcase.sh       # http://localhost:8502
```

### Facilitator UI (`apps/facilitator_ui.py`)
Login-protected facilitator tool for running ECBA study sessions with timer, slide viewer, discussion prompts, and session notes.

```bash
bash scripts/start_facilitator.sh          # http://localhost:8501
```

See [`apps/README_board_showcase.md`](apps/README_board_showcase.md) and [`apps/README_facilitator.md`](apps/README_facilitator.md) for details.

## Role Agents

Role-based AI agents for board officers. Invoke via `agents-cli`:

```bash
PYTHONPATH=. python -m agents.agents_cli role fundraising --csv-file data/donors.csv
PYTHONPATH=. python -m agents.agents_cli role membership --csv-file data/members.csv
PYTHONPATH=. python -m agents.agents_cli role communications --json-file data/ctx.json
PYTHONPATH=. python -m agents.agents_cli role professional_development --json-file data/skills.json
PYTHONPATH=. python -m agents.agents_cli role operations --json-file data/ops.json
PYTHONPATH=. python -m agents.agents_cli role accelerator --json-file data/apps.json
```

| Agent | Skills |
|-------|--------|
| President | Agenda generation, brief summarizer |
| Secretary | Action item extraction from meeting notes |
| Treasurer | Budget summary from spreadsheets |
| Fundraising | Grant/donor pipeline support |
| Membership | Member onboarding and retention |
| Communications | Newsletter drafts, event copy |
| Operations | Ops task coordination |
| Accelerator | Career accelerator program support |
| Professional Development | PD planning and recommendations |

## Scheduler

APScheduler-backed job scheduler with SQLite persistence, retry/backoff, and CLI controls.

```bash
PYTHONPATH=. python -m agents.agents_cli scheduler start
PYTHONPATH=. python -m agents.agents_cli scheduler run-once <job_id>
PYTHONPATH=. python -m agents.agents_cli scheduler stop
```

## Ingest Pipeline

Converts DOCX/PDF/PPTX files to Markdown and ingests them into the knowledge base. Includes web scrapers for IIBA event pages and partner/job listings.

```bash
PYTHONPATH=. python -m ingest.ingest_cli ingest --src etn/
```

### Template generation

Templates are plain Markdown (`.md`) files with `{{ key }}` placeholders. Generate from a stored context JSON:

```bash
python generate_cli.py -t email_template.md --project etn east_tn_business_plan_2025 -o out/email.md
```

### Watcher: approved_source_id

The folder and Drive watchers can be started with an approvals guard:

```bash
agents-cli watch --path ./inbox --approved-source-id sample_partner
agents-cli watch-drive --folder-id <FOLDER> --approved-source-id sample_job
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # add ANTHROPIC_API_KEY and other keys
```

## Testing

```bash
pytest tests/                    # 70 unit + integration tests
pytest tests/test_facilitator_playwright.py  # UI tests (requires running app)
```

## Architecture

See `DESIGN.md` for the full architecture. Key modules:

```
agents/          — role agents, scheduler, LLM adapter, PII redactor, observability
apps/            — Streamlit apps (board showcase, facilitator UI, shared utilities)
ingest/          — DOCX→MD converter, scrapers, storage, templates
integrations/    — Google Drive client and OAuth helper
etn/             — ECBA case study content and curriculum materials
config/          — Approved sources registry
```
