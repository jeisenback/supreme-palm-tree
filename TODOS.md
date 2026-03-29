# TODOS

Last updated: 2026-03-29 (Dynamic Style Guide Rule Extraction shipped)

---

## P2

### ~~Dynamic Style Guide Rule Extraction~~ ✓ SHIPPED 2026-03-29
**What:** ~~Build a parser that reads style rule definitions from `etn/ECBA_CaseStudy/Facilitator/ECBA_Style_Guide.md` and returns a `StyleRule` list — replacing the 4 hard-coded rules in `apps/content_types.py`.~~

**Status:** Done. `parse_style_rules()` added to `frontmatter_utils.py`. `## MACHINE-READABLE STYLE RULES` YAML section added to style guide. `content_types.py` calls `_load_style_rules()` at startup with hardcoded fallback.

---

### Career Accelerator + Panel Event Session Metadata Migration to YAML

**What:** After Career Accelerator sessions are authored and published in Sprint 5, migrate their session metadata (type, subtype, facilitator, agenda, homework) to YAML files consistent with the ECBA session YAML format established in Sprint 5.

**Why:** Consistency — all session types managed the same way. No code change needed to add a new session type once the YAML schema is defined.

**Pros:** Complete single-source-of-truth for all session metadata across ECBA, Career Accelerator, and Panel events.

**Cons:** Only meaningful after CA content is authored. Premature if done before content exists.

**Context:** Sprint 5 migrates ECBA sessions (1–5) to `etn/ECBA_CaseStudy/sessions/session_N.yaml`. CA and panel sessions are new to Sprint 5 — define their schema after seeing what metadata the facilitator actually needs. Schema location: `etn/career_accelerator/sessions/` and `etn/templates/panel_event/sessions/`.

**Depends on:** Sprint 5 Career Accelerator content authoring. | **Effort:** S (human) → S (~15min CC) | **Priority:** P2

---

### Cross-Session Learner Tracking

**What:** Attendance data model + learner dashboard showing: sessions attended per member, homework submitted, estimated ECBA exam readiness score.

**Why:** Enables the chapter to demonstrate measurable outcomes for board reporting, IIBA chapter metrics, and the 2026 Pilot Outcomes Summary (Q4 deliverable per roadmap).

**Pros:** High value for board; enables AI coaching whisper (Phase 2 from CEO plan); feeds into 2027 scaling decisions.

**Cons:** Requires schema design with PII implications (names + attendance records = sensitive). Needs a data model decision: SQLite vs CSV vs JSON.

**Context:** Attendance CSV export per session is already in the Consolidated Plan ops checklist (`data/attendance/YYYYMMDD_session.csv`). This TODO ingests those CSVs into a persistent learner record. Start with: ingest script → SQLite → dashboard in `board_showcase.py` or new `apps/learner_dashboard.py`. Deferred from Sprint 4 due to schema design requirement.

**Depends on:** Sprint 5 published content + attendance CSV export flow. | **Effort:** L (human) → M (~45min CC) | **Priority:** P2

---

## P3

### Hosted Deployment (Web-Accessible Content Studio)

**What:** Deploy Content Studio and Facilitator UI to a hosted environment (Render, Fly.io) so non-technical board members can author content from a browser without running the app locally.

**Why:** Currently, authoring requires `streamlit run apps/content_studio.py` locally — accessible only to developers. PD lead and chapter volunteers need browser access.

**Pros:** Unlocks non-technical board member participation in content creation.

**Cons:** Adds authentication requirements (OAuth or password), hosting costs, and file system → cloud storage migration.

**Context:** Sprint 5 is local-only. Render deployment exists for the facilitator app already (see `apps/README_facilitator.md`). Hosting content_studio.py requires either shared filesystem (NFS/S3) or a proper cloud storage backend replacing the `etn/` local filesystem pattern.

**Depends on:** Sprint 5 content authoring working locally first. | **Effort:** XL (human) → L (CC) | **Priority:** P3
