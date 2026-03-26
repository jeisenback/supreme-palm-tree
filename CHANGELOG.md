# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1.0] - 2026-03-23

### Added
- **Board Showcase app** (`apps/board_showcase.py`) — clean no-login Streamlit presentation of the ECBA certification study program for IIBA East TN board members; 6 sections: hero, curriculum timeline, slide cards, interactive MCQ, TrailBlaze narrative, document browser
- **Shared utilities module** (`apps/shared.py`) — extracts SESSIONS data, file I/O helpers, slide parser, and linkify utility shared between facilitator UI and board showcase
- **Brand theme** (`.streamlit/config.toml`) — IIBA East TN orange/navy/teal brand applied globally to all apps
- **Board showcase startup script** (`scripts/start_board_showcase.sh`) — launches board showcase on port 8502
- **Playwright CI workflow** (`.github/workflows/playwright-ci.yml`) — automated UI tests on PR
- **APScheduler SQLite jobstore** — jobs survive process restarts via SQLite persistence; `skip_persist` flag for ephemeral jobs
- **Scheduler retry/backoff** — persisted retry state with exponential backoff
- **Scraper approval registry** — runtime approval enforcement for scrapers; CLI approval management
- **Role agents** — Fundraising, Membership, Communications, Operations, Accelerator, Professional Development skills with CLI hooks
- **Google Drive integration** — DriveClient with OAuth support, folder watcher with persistence, transcript processor
- **Weekly board update generator** — human approval gate, Drive upload, CLI

### Changed
- `apps/facilitator_ui.py` — modernized: `st.experimental_rerun()` → `st.rerun()`, `st.experimental_get_query_params()` → `st.query_params`, removed deprecated shims, timer uses JS instead of `time.sleep()`, discussion prompts use session-specific data, notes/actions/complete gated by login, prototype labels removed
- `agents/scheduler.py` — preserves persisted runtime state during load

### Fixed
- `apps/board_showcase.py` — removed unused `MONTH_SESSION_MAP` import
- Scheduler persistence tests — fixed to handle skip_persist flag correctly
