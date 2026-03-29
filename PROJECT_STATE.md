# Nonprofit Tool — Project State Overview
**As of 2026-03-29** (Sprint 5 complete)

---

## Executive Summary

The nonprofit_tool is a modular curriculum and operations platform for IIBA East Tennessee, combining:
- **Facilitator UI** (`apps/facilitator_ui.py`): live session controls, published-only filter, Panel Mode
- **Content Studio** (`apps/content_studio.py`): Gap Radar, editor, AI first-draft generator
- **Board Showcase** (`apps/board_showcase.py`): no-login program presentation with live learner outcomes
- **Learner Dashboard** (`apps/learner_dashboard.py`): attendance tracking, readiness score, heatmap
- **Content development** pipeline (ingest, scrapers, templating, generation)
- **Role agents**: president/secretary/treasurer skills with LLM-safe fallbacks

**Current Sprint:** Sprint 5 — Complete ✓
**Key branch:** `main`
**Next:** P2 CA+Panel YAML migration (blocked on CA content authoring); P3 Hosted Deployment (Content Studio / Learner Dashboard)

---

## 1. Facilitator UI (`apps/facilitator_ui.py`)

### Session Lifecycle Views
- **Participant view** (public URL, no `?facilitator=1`):
  - Welcome screen with auto-poll (5s refresh, no Streamlit flicker)
  - Name entry → join session
  - Live slide viewer (polls for slide_idx updates)
  - Post-session exit screen

- **Facilitator view** (with `?facilitator=1` param + GitHub OAuth):
  - Pre-session readiness checklist with 5 gated checks:
    1. Facilitator logged in ✅ (added Sprint 3)
    2. Slide deck file exists
    3. Events CSV present
    4. Case study context loaded
    5. **Slide deck is parseable** (parse_slides smoke test) ✅ (P2 TODO, completed in current session)
  - Active session controls: headcount display, End Session button
  - Post-session export: markdown download + session reset
  - Slide navigation: keyboard shortcuts N/P/T and arrow keys

### Content Authoring Module (`_render_content_authoring`)
- **Sessions Editor tab**:
  - Edit session title, agenda, homework, discussion prompts, practice questions (JSON)
  - Saves to `etn/outputs/sessions.json` (overrides `shared.py` defaults)
  - Reset to defaults option

- **AI Draft Generator tab**:
  - LLM-powered slide deck generator (Anthropic Claude Sonnet 4.6)
  - Topic + num slides + audience level → MD format with Slide N headers
  - Editable draft, save to variant folder
  - Falls back gracefully if LLM disabled

- **Slide Upload tab**:
  - File uploader for .md/.txt decks
  - Saves directly to variant folder

### Session State Storage
- **`session_live.json`**: `{session_id, slide_idx, slide_file, started_at, ended_at, ...}`
- **`attendees/*.json`**: Per-participant `{name, joined_at, uuid}`
- **`facilitator_notes.csv`**: Facilitator notes table (event_title, facilitator, step, note, completed, timestamp)
- **`facilitator_session.json`**: Persistent user session for OAuth token + expiry

### Key Functions in `shared.py`
| Function | Purpose |
|----------|---------|
| `find_variants()` | Locate case study variant folders (`ECBA_CaseStudy*` with TrailBlaze_MasterContext.md) |
| `load_master_context()` | Load case study context from variant |
| `find_slide_deck()` | Find slide deck file (.md/.txt) in variant |
| `find_documents()` | Recursively find all docs (.md, .txt, .csv, .json, .pdf, .xlsx) in variant |
| `parse_slides()` | Parse markdown into slide objects with title, body, timing, facilitator notes |
| `linkify_content()` | Convert document references to Streamlit query params |
| `get_session_reveal()` | (TBD) Render individual slide with index |
| `render_slide_body()` | (TBD) Format slide body for display |
| `read_live_session()` | Load active session JSON (with error handling for corrupt files) |
| `write_live_session()` | Persist session state |
| `read_attendees()` | Load all attendee records from `attendees/` |
| `load_sessions_override()` | Load session content overrides from `sessions.json` |
| `save_sessions_override()` | Persist session overrides |
| `load_events()` | Load events CSV; fallback to sample data |
| `save_note()` | Append facilitator note to `facilitator_notes.csv` |

### Session Definitions (`shared.SESSIONS`)
5 sessions defined with:
- Title, agenda items, homework, discussion prompts, practice questions (MCQ w/ answer key)
- Overridable via `sessions.json`

---

## 2. Shared Utilities (`apps/shared.py`)

### Content Manipulation Functions
- **`linkify_content(content, docs, base_param)`**: Convert markdown links + bare doc names to Streamlit query params for document navigation
- **`parse_slides(md_text)`**: Parse slide deck markdown (headers: "Slide N", "Appendix") into list of slide objects:
  ```python
  {
    'title': str,          # extracted from header
    'body': str,           # remainder of slide
    'timing': str | None,  # e.g. "[15:00]" or "10 min"
    'notes': list[str]     # [FACILITATOR: ...] blocks
  }
  ```

### Templating & Generation
- **`render_template(template_text, context)`**: Simple `{{ key }}` placeholder substitution (supports dot notation & list indexing)
- **`load_template(path_or_text)`**: Load template from file or use raw text
- **`render_template_from_files(template_path, context_path)`**: Combined template + context file render

---

## 3. Content Development Ecosystem

### Agents Module (`agents/`)
| Module | Status | Purpose |
|--------|--------|---------|
| `llm_adapter.py` | ✅ Done | Provider interface + Anthropic adapter + NoOp fallback (when ANTHROPIC_API_KEY not set) |
| `pii_redactor.py` | ✅ Done | Text + context redaction for emails, phones, custom patterns |
| `skills/president.py` | ✅ Done (PoC) | Meeting agenda generator + LLM summarizer |
| `skills/secretary.py` | ✅ Done (PoC) | Action item extractor |
| `skills/treasurer.py` | ✅ Done (PoC) | Finance summary generator |
| `templating.py` | ✅ Done | Simple placeholder renderer (reused from `ingest/`) |
| `scheduler.py` | ✅ Done (Production) | APScheduler wrapper with SQLite jobstore, backoff, runtime state persistence |
| `agents_cli.py` | ✅ Done | CLI entrypoint: ingest, scrape, agent run, watch, schedule |
| `orchestrator.py` | ❌ Not yet | Router for triggers → role agents (planned Phase 2) |

### Ingest Pipeline (`ingest/`)
| Module | Status | Purpose |
|--------|--------|---------|
| `converters.py` | ✅ Done | DOCX → HTML → MD + assets; PDF text extraction; CSV/XLSX parsing |
| `storage.py` | ✅ Done | Normalize & store MD + JSON context + assets to disk |
| `generator.py` | ✅ Done | Render templates with stored context JSON |
| `templates.py` | ✅ Done | Template loader + simple placeholder renderer |
| `ingest_cli.py` | ✅ Done | CLI: `ingest --src file --out dir` |
| `generate_cli.py` | ✅ Done | CLI: generate documents from templates + context |

### Scrapers (`ingest/scrapers/`)
| Module | Status | Purpose |
|--------|--------|---------|
| `base_scraper.py` | ✅ Done | robots.txt checking + per-host rate limiting (1s default) |
| `event_scraper.py` | ✅ Done (PoC) | CSS selector-based event parser (title, date, location) |
| `job_scraper.py` | ✅ Done (PoC) | Job posting scraper |
| `partner_scraper.py` | ✅ Done (PoC) | Partner organization scraper |
| `scraper_registry.py` | ✅ Done | Config registry: store site URLs, CSS selectors, rate limits |
| `register_defaults.py` | ✅ Done | Pre-registered scraper configs for IIBA events, job boards, partners |
| `integrate.py` | ✅ Done | Entry point for common scraping scenarios |

### Board Showcase (`apps/board_showcase.py`)
- **Standalone public presentation** of ECBA certification program (no login)
- Hero section, session previews, case study variants selector
- Document library viewer (inline or linkified)
- Branded CSS (Roboto Condensed + IBM Plex Sans)

---

## 4. Current Sprint 4 Status: Chapter Portability + Course Package Export

### Branch: `feat/chapter-portability-export` (started 2026-03-24)

### Planned Work (Issue #58)
- **Chapter portability**: Support forks-and-configure deployment model
  - `chapter_config.yaml` (chapter-specific settings)
  - How-to docs for forking + overriding configs
  
- **Course package export** (ZIP):
  - Export facilitator slides + session metadata + attendee records
  - Package structure (TBD):
    ```
    course_package_2026-03-24.zip
    ├── session_metadata.json
    ├── facilitator_notes.csv
    ├── attendee_records.json
    ├── slides/
    │   ├── session_1_slides.md
    │   └── ...
    └── resources/
        ├── practice_questions.json
        └── ...
    ```

### P2/P3 Backlog (Deferred to Sprint 5+)
1. **Cross-session learner tracking** (P2, effort M, 3+ days):
   - Track learner progression across all sessions
   - Requires learner identity schema (name-based fragile; UUID cookie complex)
   - Unlocks: attendance certificates, program-level analytics
   - Decision: design schema cleanly before implementation

2. **Per-session attendee filtering** (P3, effort S, 1 day):
   - Allow filtering export to specific session/cohort (not all historical attendees)
   - Reduces PII exposure in shared packages
   - Likely post-ship usability complaint

3. **Upstream sync workflow** (P3, doc-only, 2 hours):
   - Git workflow for forked chapters to pull upstream updates
   - Doc: how to merge upstream without losing `chapter_config.yaml`

---

## 5. Test Coverage & CI

### Test Suite
- **44 tests passing** (all non-integration tests)
- Test modules:
  - `test_facilitator_ui.py` — Session lifecycle, export, checklist
  - `test_pii_redactor.py` — Email/phone masking
  - `test_skills_*.py` — Agent generation (president, secretary, treasurer)
  - `test_scheduler.py` — APScheduler + persistence
  - `test_scrapers_*.py` — Event/job/partner scrapers (HTTP fixtures)
  - `test_drive_*.py` — Google Drive integration (mocked)
  - Plus integration tests (marked `pytest -m "not integration"`)

### CI/CD
- GitHub Actions workflow (`.github/workflows/tests.yml`)
- Runs on push to `develop` and PRs
- Pattern: lint → pytest unit tests → integration tests (optional)

---

## 6. Architecture & Data Flow

### Session State Architecture
```
Facilitator UI (Streamlit)
    ↓
Reads live state: session_live.json
    ↓
Writes session events: attendees/*.json, facilitator_notes.csv
    ↓
On end session: generates session_export, resets state
```

### Content Ingest Flow
```
Local file (DOCX/PDF/CSV)
    ↓ converters.convert_*
MD + JSON context + assets
    ↓ storage.store_conversion
Disk: *.md, *.json, *_assets/
    ↓ (optional: LLM redaction, summarization)
Generator: template + context → rendered output
```

### Scraping Flow
```
URL (event/job/partner site)
    ↓ base_scraper (robots.txt + rate limit)
HTML
    ↓ event_scraper.parse (CSS selectors)
{title, date, location, source_url}
    ↓ storage (normalized JSON)
Disk: events.json (+ metadata)
```

### Agent Flow (partially implemented)
```
Trigger (CLI, schedule, folder, email)
    ↓ orchestrator (TBD)
Role agent (president, secretary, etc.)
    ↓ fetch context from ingest storage
{context_json}
    ↓ (optional: redaction)
{redacted_context}
    ↓ llm_adapter.summarize/generate
{llm_output or fallback}
    ↓ generator.render_template
{output_md}
    ↓ storage (or Google Drive)
Disk or Drive
```

---

## 7. Configuration & Secrets

### Environment Variables
| Variable | Purpose | Required |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API authentication | For LLM features (fallback: NoOp) |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID | For facilitator login |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth secret | For facilitator login |
| `OAUTH_REDIRECT_URI` | OAuth redirect URL | Facilitator login (default: `http://localhost:8501/`) |

### Config Files (TBD for Sprint 4)
- `chapter_config.yaml` (planned):
  ```yaml
  chapter_name: IIBA East TN
  chapter_id: east_tn
  coordinator_email: ...
  storage_path: etn/outputs/
  # scrapers override defaults
  enable_event_scraping: true
  ```

- `ingest/scrapers/scraper_registry.py` (current):
  ```python
  REGISTRY = {
      'iiba_events': {
          'url': 'https://easttennessee.iiba.org/events',
          'parser': 'event',
          'selectors': {...}
      },
      ...
  }
  ```

---

## 8. What's Missing / Next Steps

### Sprint 4 (In Progress)
- [ ] `chapter_config.yaml` schema & example
- [ ] Course package export ZIP builder
- [ ] Per-chapter customization logic in facilitator UI
- [ ] Documentation: fork-and-configure workflow

### Sprint 5+ (Backlog)
- [ ] Learner identity schema design (name vs UUID vs email)
- [ ] Cross-session learner tracking module
- [ ] Per-session export filtering
- [ ] Upstream sync documentation
- [ ] Full orchestrator (trigger router)
- [ ] Production deployment guide

### Known Gaps
1. **No cross-session learner tracking** — attendance is per-session only
2. **No learner outcome analytics** — cannot see program-level progress
3. **No SCORM export** — would require learner schema + metadata
4. **No real-time sync** — uses 3-5s poll intervals (acceptable for study sessions)
5. **Limited scraper extensibility** — CSS selectors only (no Playwright for JS-heavy sites)
6. **No folder-watcher enforcement** — approvals enforcement is CLI-only (Sprint 2 carry-forward)

---

## 9. Key Files & Structure

```
apps/
  facilitator_ui.py          → Main Streamlit app (sessions, content authoring)
  board_showcase.py          → Public-facing program showcase
  shared.py                  → Session constants, content utilities, I/O helpers

agents/
  llm_adapter.py             → LLM provider interface + adapters
  pii_redactor.py            → Email/phone/custom redaction
  scheduler.py               → APScheduler + persistence layer
  templating.py              → Template rendering (simple {{ }} substitution)
  agents_cli.py              → CLI entry points
  skills/
    president.py             → Agenda + summary generation
    secretary.py             → Action item extraction
    treasurer.py             → Finance summaries

ingest/
  converters.py              → DOCX/PDF/CSV → MD + JSON + assets
  storage.py                 → Normalized disk storage
  generator.py               → Template + context → output
  templates.py               → Template loader + renderer
  ingest_cli.py              → CLI: ingest --src
  generate_cli.py            → CLI: generate from template
  scrapers/
    base_scraper.py          → robots.txt + rate limiting
    event_scraper.py         → Event page parser
    job_scraper.py           → Job posting parser
    partner_scraper.py       → Partner org parser
    scraper_registry.py      → Config registry
    integrate.py             → High-level scraping entry point

tests/
  test_facilitator_ui.py     → Session lifecycle + export tests
  test_pii_redactor.py       → Redaction logic tests
  test_skills_*.py           → Agent generation tests
  test_scheduler.py          → APScheduler persistence tests
  test_*_scraper*.py         → Scraper tests (HTTP fixtures)

etn/
  ECBA_CaseStudy_*/          → Case study variants (TrailBlaze_MasterContext.md, slides, docs)
  outputs/
    iiba_events_parsed.csv   → Parsed event listings
    facilitator_notes.csv    → Session facilitator notes
    facilitator_session.json → Persistent user session
    session_live.json        → Active session state
    sessions.json            → Session content overrides
    attendees/               → Per-participant records (*.json)

docs/
  energy_options_adlc.md     → (Planning doc)
  partner_brief.md           → (Planning doc)
  scheduler.md               → Scheduler documentation

config/
  (TBD for Sprint 4)         → chapter_config.yaml + examples

DESIGN.md                      → Architecture design document
HEARTBEAT.md                   → Sprint state tracker
SESSION.md                     → Current session notes
TODOS.md                       → Prioritized backlog items
TASKS.md                       → Task definitions (Phases 0–5)
REQUIREMENTS.md                → Functional/non-functional requirements
README.md                      → Project quickstart & overview
```

---

## 10. UI/UX Capabilities

### Session UI Components (Streamlit)
- Split-view: facilitator controls (left sidebar) + slide viewer (main)
- Meta-refresh polling (3–5s intervals, no Streamlit re-renders)
- Participant name entry → join session
- Live attendee roster with duplicate name handling
- Slide navigation: keyboard shortcuts (N/P/T/Arrows)
- Post-session markdown export + download
- Session reset with 2-step confirmation

### Content Editor Components
- JSON editor for practice questions
- Textarea editors for agenda, homework, prompts
- MDN text area for AI-generated slides (editable before save)
- File uploader for slide deck replacement
- AI draft generator with configurable # slides + audience level

### Public Showcase Components (board_showcase.py)
- Hero section with branded header
- Case study variant selector + preview
- Document library browser
- Session calendar view (TBD)

---

## 11. Deployment & Operations

### Development Setup
```bash
cd c:\tools\nonprofit_tool
python -m venv .venv
.venv\Scripts\activate               # Windows
pip install -r requirements.txt
```

### Running the Facilitator UI
```bash
streamlit run apps/facilitator_ui.py
```

### Running the Board Showcase
```bash
streamlit run apps/board_showcase.py
```

### Running Tests
```bash
pytest tests/ -m "not integration"    # Unit tests only
pytest tests/                          # All tests including integration
pytest tests/test_facilitator_ui.py   # Specific test module
```

### Running CLI Tools
```bash
# Ingest a document
python -m agents.agents_cli ingest --src path/to/input.docx --out etn/outputs/

# Scrape event data
python -m agents.agents_cli scrape --source-id iiba_events

# Generate from template
python -m ingest.generate_cli -t template.md --context context.json -o output.md

# Run scheduled job
python -m agents.agents_cli schedule --url "https://site.com/job" --parser job
```

---

## Summary: What Exists vs. What's Needed

### Fully Implemented ✅
- Session lifecycle (Go Live → participant sync → End → export)
- Pre-session readiness checklist (with parse_slides smoke test)
- Participant attendance tracking + facilitator notes
- Slide deck parsing + navigation (keyboard shortcuts)
- Content authoring: sessions editor, AI draft generator, slide upload
- LLM adapter (Anthropic + NoOp fallback)
- PII redaction (emails, phones, custom patterns)
- Document ingestion (DOCX, PDF, CSV/XLSX)
- Web scraping (base infrastructure + event/job/partner parsers)
- Template rendering (simple {{ }} substitution)
- Scheduler with persistence + backoff
- Comprehensive test suite (44/44 passing)

### In Progress (Sprint 4) 🔄
- Chapter portability (chapter_config.yaml)
- Course package export (ZIP builder)

### Not Yet Implemented ❌
- Cross-session learner tracking / learner identity schema
- Per-session export filtering
- Full orchestrator (trigger routing)
- Folder-watcher approval enforcement (Sprint 2 carry-forward)
- SCORM/LMS export
- Real-time WebSocket sync (note: polling is acceptable for current use case)
- Upstream fork sync documentation
- Advanced scraper features (Playwright for JS-heavy sites)

