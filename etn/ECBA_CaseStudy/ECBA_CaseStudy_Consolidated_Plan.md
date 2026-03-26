# ECBA Case Study — Consolidated Recommendations & Delivery Plan

Purpose
- Provide a single actionable plan synthesizing recommendations for Members, President (Board), Facilitators, and Professional Development (PD) leads.
- Make immediate operational changes and produce one‑page briefs each stakeholder can review.

Summary Verdict
- Instructional design is strong (spacing, ARCS, progressive reveal, SME practice). Risks are incomplete session materials and missing operational wiring (registration fields, attendance exports, survey text export). Priorities: finish content, add quick operational changes, and enable agent automation.

Immediate (0–2 weeks)
- Implement structured registration fields: member status, job title, planned ECBA date, 5‑item self‑assessment. (Owner: Communications + Membership)
- Make rubric visible at assignment time (Workshop Handout update). (Owner: Facilitator)
- Create facilitator 'fail‑safe' micro‑routine and SME fallback script. (Owner: PD Lead)
- Create one consolidated plan file and one‑page briefs for each perspective. (Owner: Project / PD)

Short Term (2–6 weeks)
- Re-run parser and finalize event / page artifacts (existing work). (Owner: Tech)
- Update `communications` templates so agents can draft: registration announcements, 5‑day previews, day‑of engagement posts, post‑session recaps. (Owner: Communications + Tech)
- Start attendance CSV export process per session and a simple attendance ingestion format for agents. (Owner: Membership)
- Pilot automated board brief generation from session data (monthly). (Owner: President agent + PD)

Medium Term (6–12 weeks)
- Build Sessions 2–5 content to the same fidelity as Session 1 (Slides, PracticeQuestions, Facilitator_Script, Facilitator_Answers). Prioritize Session 2 first. (Owner: PD Lead)
- Implement cohort calibration: require intake self‑assessment at registration; run pre‑series cohort analysis to flag weak domains and suggested focus. (Owner: professional_development agent)
- Deliver facilitator training session covering timing recovery, probing questions, and rubric use. (Owner: PD)

Success Metrics
- Attendance: ≥8 per session
- Homework submission: ≥60% of attendees
- Non-member attendance: ≥2 per session
- ECBA exam registrations from cohort: ≥3 by series end
- Membership conversion: ≥1 per cohort

Stakeholder‑Specific Plans

Members (Learners)
- What they get: Five-session case arc with practice MCQs, SME exercises, and homework that builds a portfolio artifact (BACCM, RTM, solution recommendation).
- Immediate asks: complete pre-reading and self‑assessment; receive rubric at assignment time.
- Supports: Week‑0 quick start (15–20 min) and checklist, optional 30‑min homework office hours for juniors.
- Deliverables to members: Session handouts, rubric, homework bank, recommended study schedule.

President / Board
- What they care about: measurable outcomes and resource ROI.
- Deliverable: auto‑generated 1‑page board briefs per cohort (attendance trend, homework rate, member conversions, 3 risks & mitigation). Schedule: monthly cadence aligned to board meeting.
- Actions: endorse structured registration and data exports; sponsor SME identification.

Facilitators
- What they need: clear timing, exact scripting, recovery cheatsheets, rubrics, and SME fallback.
- Deliverable: one‑page facilitator 'fail‑safe' and full Facilitator_Guide per variant; rubric preview included in Workshop_Handout distribution.
- Actions: conduct a short rehearsal, confirm SME backup, verify access to session materials one week prior.

Professional Development (PD)
- What PD needs: cohort calibration, outcome analytics, and alignment to chapter goals.
- Deliverables: cohort pre‑series report (self‑assessment summary), mid‑series check (homework+MCQ performance), end‑series impact report (attendance, exam registrations, conversion).
- Actions: enforce intake form, request attendance CSV exports, set up agent checks to flag dropouts and low homework rates.

Operational Checklist (minimum viable)
1. Registration form fields: member status, job title, planned exam date, 5‑item self‑assessment (1–5), opt‑in for homework reminders.
2. Attendance export: CSV per session with columns: session_id, date, name, member_id/email, attended (Y/N). Save to `data/attendance/YYYYMMDD_session.csv`.
3. Survey export: facilitator exports free‑text responses as single text file per session for secretary agent processing.
4. SME fallback: pre-written role script and 'drop‑in' SME shortlist (3 names) for each session; if SME cancels <72h, run commit prompt exercise.

Deliverables I will create next (if you approve)
- `ECBA_CaseStudy_Consolidated_Plan.md` (this file)
- Four one‑page briefs (Members, President, Facilitators, PD) saved to `etn/ECBA_CaseStudy/briefs/`
- `Operational_Checklist.md` with copy/paste fields for MemberNova and attendance CSV schema.

Questions / Decisions Needed
1. Approve structured registration fields and where to update the MemberNova form (who will implement?).
2. Confirm SME fallback shortlist owner (PD or Facilitator?).
3. Approve building Session 2 materials as immediate content priority.

Next Step
- If you confirm, I'll produce the four one‑page briefs and the operational checklist next. Reply with which brief to start with or authorize all at once.

---
File created: etn/ECBA_CaseStudy/ECBA_CaseStudy_Consolidated_Plan.md
