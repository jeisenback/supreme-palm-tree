# Design Document: Board Agents Platform

## TL;DR
Modular agent system composed of an orchestrator, per-role agents (skills), an LLM adapter (Anthropic), PII redaction layer, and an extended ingest pipeline that includes web scrapers. Reuse existing `ingest/` conversion, storage, and templating utilities; add `ingest/scrapers/` and `agents/` packages.

## Architecture Components
- Agent Orchestrator (`agents/orchestrator.py`)
  - Receives triggers (CLI, schedule, folder events, email), routes to appropriate role agent or system task.
- Role Agents (`agents/skills/*.py`)
  - `PresidentAgent`, `TreasurerAgent`, `SecretaryAgent`, etc.
  - Each implements `handle_trigger(trigger_type, payload)` and role-specific helper methods.
- LLM Adapter (`agents/llm_adapter.py`)
  - Provider interface with methods `summarize(text, params)`, `generate(prompt, params)`.
  - Implementation: `anthropic_adapter` using env `ANTHROPIC_API_KEY` and feature flagging to disable external calls.
- PII Redactor (`agents/pii_redactor.py`)
  - Identifies/masks email, phone, SSN, and custom fields. Exposes `redact(text)` and `redact_context(context)`.
- Ingest Pipeline (reuse + extend `ingest/`)
  - Use `ingest/converters.py` and `ingest/storage.py` for local docs.
  - Add `ingest/scrapers/` for external content with unified output format.
- Scraping Module (`ingest/scrapers/`)
  - `base_scraper.py`: robots.txt check, rate-limiter, fetcher, caching.
  - `event_scraper.py`, `job_scraper.py`, `partner_scraper.py`: parse HTML into canonical context.
  - `scraper_registry.py`: store site configs, CSS/XPath rules, optional JS-mode flag.
- Templates & Generation (`ingest/generator.py`, `ingest/templates.py`)
  - Reuse simple templates for emails/briefs; agents populate context and call `generate_from_context_file`.
- CLI & Triggers (`agents_cli.py`) 
  - Commands: `ingest --src`, `scrape --source-id`, `agent run --role president --action agenda`, `watch`, `schedule`.

## Data Flow
1. Trigger received by Orchestrator.
2. If input is a file: call `ingest.converters.convert_file_to_md_context` → `ingest.storage.store_conversion`.
3. If input is a scrape: `scrapers` produce canonical JSON → stored via `ingest.storage`.
4. Agent retrieves JSON context, optionally redacts, calls LLM via `llm_adapter` (if enabled), then renders templates with `ingest/generator`.
5. Output saved to disk and optionally pushed to Google Drive.

## Config & Secrets
- `config/agents.yaml` schema:
  - `provider`: anthropic|none
  - `providers`:
    - `anthropic`: enabled: bool
  - `scraper_sources`: list of {id, url, parser: event|job|partner, rate_limit, allowed: bool}
  - `storage`: local_out_dir, google_drive: {enabled, creds_path}

Secrets via env vars: `ANTHROPIC_API_KEY`.

## File Layout (proposed additions)
- `agents/`
  - `__init__.py`
  - `orchestrator.py`
  - `agent_base.py`
  - `llm_adapter.py`
  - `pii_redactor.py`
  - `skills/president.py`, `skills/treasurer.py`, `...`
  - `agents_cli.py`
- `ingest/scrapers/`
  - `__init__.py`, `base_scraper.py`, `event_scraper.py`, `job_scraper.py`, `partner_scraper.py`, `scraper_registry.py`
- `config/agents.yaml` (example)
- `tests/` — unit and integration tests

## Data Models
See `requirements.md` for canonical JSON context fields. Add `scraper_source` metadata: `source_id`, `scraped_at`, `crawl_id`.

## Security & Privacy
- PII redaction enforced by default.
- Option to mark certain sources as sensitive; sensitive data never leaves local environment unless explicitly allowed.
- Maintain an audit log of LLM requests (prompt hash, redacted input, timestamp) stored locally.

## Observability
- Structured logging (JSON) with levels.
- Basic metrics: ingestion count, scrape success/failures, LLM request counts.

## Testing Strategy
- Unit tests for each adapter and redactor.
- Integration tests using recorded HTTP fixtures for scrapers and sample docs for converters.
- End-to-end test: ingest sample doc + scrape sample site → agent generates an email draft.

## Alternatives Considered
- Use Jinja2 for templates (rejected for now to minimize scope; revisit after PoC).
- Use Playwright for scraping by default (rejected; make optional due to resource cost).
