# Requirements: Board Agents Platform

## Purpose
Provide a modular agent system to help manage the nonprofit's board responsibilities, ingest organizational context (files + web), generate communications and briefs, capture meeting minutes/action items, surface events/jobs/partners, and support role-specific workflows.

## Functional Requirements
- Ingest local documents (DOCX, PDF, XLSX) and convert to canonical Markdown + JSON context via existing `ingest/` pipeline.
- Ingest external content via web scraping (events, partner pages, job postings) with source metadata.
- Provide role-specific agents (President, Vice President, Secretary, Treasurer, Fundraising, Membership, Communications, Professional Development, Operations, Accelerator Lead) that can:
  - Generate templated emails, event briefs, and meeting agendas using templates.
  - Summarize and extract action items and owners from meeting notes.
  - Produce finance summaries for Treasurer (CSV/XLSX ingestion + basic aggregates).
  - Produce membership and renewal reports for Membership Chair.
- Provide triggers: CLI, folder watcher, scheduled jobs (cron), email inbound parsing (basic), and on-demand scraping.
- Expose a CLI entrypoint `agents_cli.py` for manual workflows and administrative commands.
- Store outputs on local disk; support optional export to Google Drive.

## Non-functional Requirements
- Security & Privacy
  - PII redaction before any external LLM calls; default mask for emails/phones/SSNs.
  - Option to run without LLMs (manual-only mode).
  - Credentials (e.g., Anthropic API key) provided via environment variables and never committed.
- Reliability
  - Respect robots.txt and rate limits for scraping; retry with exponential backoff.
  - Deterministic storage paths and file naming for reproducible outputs.
- Testability
  - Unit tests for adapters, scrapers, and redaction logic.
  - Integration tests with recorded HTTP fixtures and sample documents.
- Maintainability
  - Modular code organization (`agents/`, `ingest/scrapers/`, `agents/skills/`) and clear config schema.

## Constraints & Dependencies
- Base Python dependencies from `requirements.txt`. Additional libraries: `requests`, `beautifulsoup4` (already present), `pytest` for tests, `freezegun` or `responses` for HTTP fixtures, optional `playwright` or `selenium` for JS-heavy scraping.
- No LLM provider config in repo; Anthropic selected by plan — requires `ANTHROPIC_API_KEY` env var.
- No CI currently; plan includes GitHub Actions for tests.
- Platform: development on Windows is supported; code must use `pathlib`.

## Data & Schema
Canonical JSON context for each ingested item should include:
- `id` (string, canonicalized URL or filename)
- `source` (local|external)
- `source_url` (optional)
- `type` (document|event|job|partner)
- `title`
- `summary` (short)
- `content` (markdown)
- `metadata` (dict: date, location, contact, scraped_at)
- `assets` (if any)

## Acceptance Criteria (High-level)
- PoC CLI ingests a sample DOCX and outputs Markdown+JSON to `out/`.
- PoC scraper ingests a sample event page and produces a JSON context with `type=event` and `metadata.date`.
- PII redactor masks emails/phones before any external LLM call.
- Unit tests run in CI and pass.
