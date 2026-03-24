# HEARTBEAT

> **The canonical source of sprint state. Never edit Sprint Issues table rows after they're set.
> Append-only sprint notes at the bottom of each sprint block.**

---

## Project

**Repo:** `nonprofit_tool`
**Platform:** IIBA East Tennessee — Board Agents Platform
**Main branch:** `main`
**Develop branch:** `develop` (merge target for PRs)

---

## Current Sprint

| Field | Value |
|-------|-------|
| Sprint | 3 |
| Status | **COMPLETE** |
| Goal | Facilitator UI — session lifecycle, participant sync, content authoring, keyboard shortcuts, post-session export |
| Started | 2026-03-23 |
| Target | 2026-04-06 |
| Active Branch | `feat/facilitator-ui-expansion` |
| Active Issue | #51 |

---

## Sprint 3 Issues

| # | Title | Branch | Status |
|---|-------|--------|--------|
| 51 | facilitator: session lifecycle — Go Live, participant sync, attendance tracker | `feat/facilitator-ui-expansion` | done |
| 52 | facilitator: pre-session readiness checklist gates Go Live button | `feat/facilitator-ui-expansion` | done |
| 53 | facilitator: post-session markdown export | `feat/facilitator-ui-expansion` | done |
| 54 | facilitator: unified keyboard shortcuts for slide navigation (N/P/T/Arrow keys) | `feat/facilitator-ui-expansion` | done |
| 55 | facilitator: content authoring module — sessions editor, AI draft generator, slide upload | `feat/facilitator-ui-expansion` | done |
| 56 | chore: app-layer tests for facilitator UI + fix 3 critical silent-failure gaps | `feat/facilitator-ui-expansion` | done |

---

## Sprint 2 Issues (Parked — carry forward to next opportunity)

| # | Title | Branch | Status |
|---|-------|--------|--------|
| 42 | scheduler: add persistence and retry logic | `feat/scheduler-preserve-runtime-state` | in-progress |
| 43 | observability: add scheduler metrics & health endpoints | `feat/scheduler-observability` | open |
| 41 | ingest/scrapers: enforce approvals in watcher and other manual runners | `feat/approved-sources-enforcement` | in-progress |
| 39 | tests: add HTTP-fixture integration tests using responses | `feat/http-fixture-tests` | in-progress |
| 44 | security: document secrets handling and required env vars | `feat/secrets-guidance` | open |
| 40 | chore: update PR #38 metadata | — | open |

---

## Sprint 1 Issues (Completed)

| # | Title | Status |
|---|-------|--------|
| Phase 0–1 | Core infra, agents package, LLM adapter, PII redactor | done |
| Phase 2 | Scrapers, storage integration | done |
| Phase 3 | Role agents: President, Secretary, Treasurer, Fundraising, Membership, Comms, PD, Ops, Accelerator | done |
| Phase 4 | Unit tests, GitHub Actions CI | done |
| 21 | Folder-watcher and scheduler hooks | done |
| 18 | Harden scheduler for production (initial APScheduler integration) | done |
| 19 | Scheduler observability (Prometheus metrics, SCHEDULER_METRICS_PORT) | done |

---

## Blockers

_None currently logged._

---

## Sprint Notes (2026-03-23, session 1)

- Session bootstrapped: created HEARTBEAT.md, SESSION.md, SESSION.md.template, docs/energy_options_adlc.md
- Branch `feat/scheduler-preserve-runtime-state` is 1 commit ahead of origin with `.secret_test_tmp` staged (needs cleanup before next commit)
- Key work already committed on this branch: APScheduler SQLite jobstore, retry/backoff, persist runtime state on load, HTTP-fixture tests, approvals enforcement, drive watcher persistence
- Branch carries a wide range of Sprint 2 work — consider scoping future branches to single issues

## Sprint Notes (2026-03-23, session 2)

- Sprint 2 parked (in-progress work on #42, #41, #39 preserved on their branches)
- Sprint 3 opened: facilitator UI expansion for ECBA study session tool
- CEO plan reviewed (SELECTIVE EXPANSION mode), eng review completed, 6 GitHub issues created (#51–#56)
- CEO plan artifact: `~/.gstack/projects/jeisenback-supreme-palm-tree/ceo-plans/2026-03-23-facilitator-ui-expansion.md`
- Test plan artifact: `~/.gstack/projects/jeisenback-supreme-palm-tree/jeise-feat-scheduler-preserve-runtime-state-test-plan-20260323-190357.md`
- Implementation branch to create: `feat/facilitator-ui-expansion` off `develop`
- Key architectural decisions: file-based session state (session_live.json + attendees/), meta-refresh polling (no st.rerun()), unified JS keyboard handler, LLM adapter upgrade to /v1/messages + claude-sonnet-4-6
- TODOS.md updated with 1 deferred item (parse_slides smoke test, #50, Phase 2)
