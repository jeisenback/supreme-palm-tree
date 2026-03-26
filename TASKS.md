# Task List: Board Agents Project

Guiding rules: each task includes a short acceptance criteria (AC) and dependencies. Mark human tasks explicitly.

## Phase 0 — Setup
1. Initialize Git repository in workspace (human)
   - Description: `git init`, add remote when provided, create initial commit with existing workspace.
   - AC: `git status` clean, remote set, initial commit present.
   - Dependencies: none
2. Add repository README and licensing note
   - AC: `README.md` updated with project summary and quickstart.

## Phase 1 — Core Infrastructure (PoC)
3. Create `agents/` package skeleton
   - AC: files `agents/__init__.py`, `agent_base.py`, `orchestrator.py`, `agents_cli.py` exist and importable.
   - Dependencies: Phase 0
4. Implement `llm_adapter.py` interface and a no-op provider (safe stub)
   - AC: unit tests verifying calls route to stub when no API key.
   - Dependencies: Task 3
5. Implement `pii_redactor.py` with basic masks for emails and phones
   - AC: unit tests show emails/phones masked in sample text.
   - Dependencies: Task 3
6. Wire CLI commands for ingestion using existing `ingest/` code
   - AC: `agents_cli.py ingest --src sample.docx` produces JSON+md in out dir.
   - Dependencies: Task 3

## Phase 2 — Scrapers & Storage Integration
7. Add `ingest/scrapers/` skeleton and `scraper_registry.py`
   - AC: registry can register a sample source and return config.
   - Dependencies: Phase 1
8. Implement `base_scraper.py` (robots.txt check + rate limit)
   - AC: respects robots.txt for a recorded fixture, rate-limit test passes.
   - Dependencies: Task 7
9. Implement `event_scraper.py` (requests + BeautifulSoup) for 1 sample event site
   - AC: parses event date/title/location into canonical JSON for sample site.
   - Dependencies: Task 7,8
10. Integrate scraped JSON into `ingest/storage.py` pipeline
    - AC: scraped item saved as consistent JSON and listed in `out/`.
    - Dependencies: Task 9

## Phase 3 — Role Agents (PoC for 3 roles)
11. Implement `skills/president.py` with: agenda generator, brief summarizer
    - AC: given meeting notes JSON, produces agenda markdown via templates.
    - Dependencies: Phase 1,2
12. Implement `skills/secretary.py` to extract action items
    - AC: extracts action items with owner and due-date from notes.
    - Dependencies: Phase 1,2
13. Implement `skills/treasurer.py` to ingest a sample spreadsheet and produce summary
    - AC: outputs a simple CSV summary and `balances.md` for sample data.
    - Dependencies: Phase 1,2

## Phase 4 — Tests, CI, and Security
14. Add unit tests for adapters, scrapers, and agents
    - AC: `pytest` runs locally and passes on changed modules.
    - Dependencies: Phase 1–3
15. Add GitHub Actions workflow to run tests on push
    - AC: workflow YAML committed to `.github/workflows/tests.yml`.
    - Dependencies: Task 14
16. Implement PII redaction into end-to-end flow and audit logs
    - AC: end-to-end test shows prompt hashed and redacted content logged.
    - Dependencies: Task 5,14

## Phase 5 — Expansion & Integrations
17. Implement folder-watcher and scheduler hooks
    - AC: scheduled scrape runs and files dropped into watch-folder are ingested.
    - Dependencies: Phase 1–3
18. Google Drive export integration (optional)
    - AC: sample file uploaded to Drive using provided creds (human step to provide creds).
    - Dependencies: Phase 1, user-provided creds
19. Add additional role agents (Fundraising, Membership, Communications, Professional Development, Operations, Accelerator)
    - AC: each role has a basic handler and a corresponding unit test.
    - Dependencies: Phase 3

## Human Tasks (explicit)
- Approve scraping of new domains (human review step).
  - AC: UI or CLI confirmation recorded in `config/sources-approved.yaml`.
- Provide remote Git URL and credentials for repo remote setup.
  - AC: `git remote -v` shows the provided URL.
- Provide Google Drive credentials if Drive export is desired.
  - AC: Drive export task passes for sample file.

## Milestones (suggested)
- M1: PoC Ingest + Scrape (Tasks 3–10 complete)
- M2: Core Role Agents (Tasks 11–13 complete)
- M3: Tests & CI (Tasks 14–15 complete)
- M4: Expanded Roles & Integrations (Tasks 17–19 complete)

## Status (2026-03-15)
- Most Phase 0–4 items implemented and unit-tested in PoC form.
- Google Drive integration and OAuth helpers added (guarded imports; creds required).
- Scheduler PoC, CLI controls, runner script, and tests added — PRs merged into `main`.
- GitHub Actions CI is active and recent runs for scheduler/CLI succeeded.

- Role agents added: Fundraising, Membership, Communications, Professional Development, Operations, Accelerator (PoC implementations with unit tests and CLI hooks).
## Next actions (recommended)
- Harden scheduler for production: add persistence (APScheduler or Celery) and retry logic.
- Improve scheduler observability: add metrics/log forwarding and health endpoints.
- Add secrets handling guidance: document required env vars and recommend Vault or GitHub Secrets.
- Expand role agents incrementally (Fundraising, Membership, Communications) with tests.
- Optional: perform an end-to-end Drive export with real credentials (human step).

If you want, I can open issues for the recommended next actions and start implementing the first one (scheduler persistence).
