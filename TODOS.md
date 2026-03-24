# TODOS

## TODO: Pre-session parse_slides smoke test

**What:** Call `parse_slides()` in the pre-session readiness checklist so a malformed slide file fails before "Go Live."

**Why:** The current MVP checklist only checks `find_slide_deck() is not None` (file exists). A `.md` file that exists but has no parseable slide headers passes the checklist but returns 0 slides for every participant during the session — the facilitator discovers this mid-session.

**Pros:** Catches malformed decks before Go Live; same function already used in the slide viewer.

**Cons:** `parse_slides()` reads and regex-scans the file (adds ~10ms to checklist). Acceptable since checklist runs once pre-session.

**Context:** CEO plan (2026-03-23-facilitator-ui-expansion.md) acknowledges this as a known Phase 2 item. MVP intentionally skips to keep checklist fast. The facilitator can verify the deck in the slide preview pane before Go Live as a manual workaround.

**Where to start:** `apps/facilitator_ui.py` — in the pre-session checklist block, add Check 5: `bool(parse_slides(slide_deck_path.read_text(encoding='utf-8')))`.

**Effort:** S (human ~30min / CC ~2min)
**Priority:** P2
**Depends on:** Facilitator UI split-view feature (this PR)

---

## TODO: Cross-session learner tracking

**What:** Track individual learner progress across all sessions in a program — attendance history, practice question scores, homework completion, cumulative session count.

**Why:** Currently attendance is tracked per-session with no linkage. A program coordinator cannot see whether a learner attended 3 of 5 sessions or how they performed across the program. This is the missing "learner outcome" layer that would make the tool meaningful for program evaluation.

**Pros:** Unlocks program-level analytics; enables attendance certificates; prerequisite for SCORM export (learner records); differentiates from a simple slide deck tool.

**Cons:** Requires schema design (a cross-session learner identifier — name-based is fragile; UUID per learner is complex for sign-in UX). Risk of PII accumulation if not handled carefully. Should not be rushed — a bad schema here creates migration pain later.

**Context:** CEO plan (2026-03-24-training-development-platform.md) explicitly deferred this. The decision: high leverage but needs proper schema design. Don't bolt it onto the file-based session state introduced in Sprint 3. Design the schema cleanly before Sprint 5+.

**Where to start:** Design a `learner_records.json` schema (or SQLite table) keyed by a stable learner identifier. The main open question is identity: require email at sign-in vs. name-only vs. UUID cookie. Resolve this before any implementation.

**Effort:** M (human ~3 days / CC ~1 hour)
**Priority:** P2
**Depends on:** Sprint 3 file-based session state (attendees/*.json) — Sprint 4 chapter portability

---

## TODO: Per-session attendee filtering in course package export

**What:** Allow a program coordinator to download a course package filtered to a specific session or program run, rather than all attendee records ever written to `attendees/`.

**Why:** With no filter, a 50-session deployment would dump all historical attendee data in every ZIP. Coordinators need data scoped to their program run.

**Pros:** Reduces PII exposure in shared packages; makes the export more useful for per-cohort reporting.

**Cons:** Requires a UI picker in the facilitator post-session panel; adds state complexity to the export flow.

**Context:** Sprint 4 course package export includes all attendee files with no filter (intentional for MVP simplicity). This is the most likely usability complaint post-Sprint 4 ship.

**Effort:** S (human ~1 day / CC ~15min)
**Priority:** P3
**Depends on:** Sprint 4 course package export

---

## TODO: Upstream sync workflow for forked chapters

**What:** Document a clear git workflow for how a chapter that forked the repo can pull upstream bug fixes and feature updates without losing their `chapter_config.yaml` customizations.

**Why:** The Sprint 4 "fork and configure" deployment model works for initial setup but leaves chapters stranded on their fork version. A non-technical coordinator cannot be expected to know `git remote add upstream` + `git merge upstream/main`.

**Pros:** Lowers the operational burden of chapter portability; prevents chapters from running stale versions.

**Cons:** None — this is a README documentation task, not a code change.

**Context:** Sprint 4 NOT IN SCOPE. The `chapter_config.yaml` file is committed to the fork and survives a merge as long as it doesn't conflict with upstream `chapter_config.yaml.example` (which should be the upstream-provided template).

**Effort:** S (human ~2 hours / CC ~10min)
**Priority:** P3
**Depends on:** Sprint 4 chapter portability
