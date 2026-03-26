# TrailBlaze Adventures — ECBA Case Study Master Plan

--- DOCUMENT GUIDE ---
What this is:   Master planning document for the full 5-session series — session structure, ECBA domain and BABOK coverage, TrailBlaze story arc, file structure, and alignment notes.
Who it's for:   Facilitator; approvers (read-only).
When to use it: Reference during series design and before each session prep. Primary guide for building Sessions 2–5 materials.
Restricted:     Yes — do not share with participants.
--- END GUIDE ---

*All abbreviations used in this document are defined in the Abbreviations section at the end.*

## Overview

### Series Structure
Five monthly sessions (April–August), each covering a set of ECBA domains and corresponding Business Analysis Body of Knowledge (BABOK) Knowledge Areas (KAs). Each session is framed through the ECBA exam lens (domains) but explicitly maps to BABOK KAs so no content gaps are left. Both lenses are labeled in every session entry.

The ECBA exam tests 9 domains. Those domains do not map one-to-one with BABOK chapters — they reflect a different organizing principle. This series bridges both: participants learn the concepts through BABOK (because that's what they're reading) and practice applying them through domain language (because that's what the exam tests). Every exercise, debrief, and question is framed through domain language first.

The monthly cadence is intentional. Participants are working professionals. One session per month gives them time to do the required reading, complete homework, and let concepts settle before the next layer is added. Compressing the series would break the spaced practice model.

### Before the Series — Session 0
An onboarding handout is distributed before Session 1: study habits, Cornell notes, retrieval practice, ECBA exam overview, and the full reading schedule. No meeting required.

Session 0 exists because the first 10 minutes of Session 1 should not be spent explaining how the series works. Participants who arrive without context slow down the room. The onboarding handout removes that problem. It also sets the expectation that this is an active learning environment — participants who read it know they will be asked to apply concepts, not just receive them.

### Session A — Core Session (90 minutes)
Each Session A follows a phase-based run-of-show. The phase tables in the Session Map show activity, purpose, and timing for each session.

The sequence is not arbitrary. Concepts are introduced with a TrailBlaze anchor so participants immediately see the application context, not an abstract definition. Guided application follows immediately — the facilitator works through a partial example with the group before releasing them to work independently. This reduces the "I don't know where to start" failure mode that kills group exercise time.

The group exercise produces a real artifact (BACCM chart, stakeholder list, problem statement, etc.). The share-out makes that work visible to the room, which triggers peer comparison and discussion — a stronger learning signal than facilitator feedback alone.

Checkpoint questions are placed mid-concept, not at the end. Their purpose is to surface misunderstanding before it compounds. If a group answers a checkpoint wrong, the facilitator adjusts before the exercise — not after.

The practice round closes with 4 timed ECBA exam-style multiple choice questions answered individually before group discussion. Individual-first matters: it replicates exam conditions and prevents participants from anchoring on the first confident voice in the group.

The homework deliverable is always an extension of in-session work, not a new task. This keeps the total effort manageable and reinforces that in-session work is worth doing well.

A 2-minute survey closes the loop for facilitator adjustments.

### Session B — SME Deep Dive (60 minutes, mid-cycle)
Approximately 2 weeks after each Session A, an internal subject matter expert (SME) co-facilitates a TrailBlaze deep dive.

The two-week gap is structural. Session A introduces a concept and gives participants a first attempt at applying it. Two weeks of living with the homework — and the questions it raises — means Session B lands when participants are ready to be challenged on what they think they understood. If Session B were the day after Session A, participants would not have had time to form the misconceptions that Session B is designed to surface.

Session B never introduces new content. The SME's job is to add friction to what the group already has — a stakeholder who gives incomplete answers, an executive who pushes back on a solution recommendation, a retrospective on a real deployment that missed its targets. This simulates what BA work actually feels like: messy inputs, competing priorities, and no clean answer. Participants leave with a more accurate model of what applying the ECBA concept looks like outside a classroom.

The SME is also a network asset. Each Session B ends with a stretch question and a debrief where the SME speaks candidly about their own experience. Participants leave with a contact, not just a concept.

- Same case, no new content — real-world friction layered on top of Session A work.
- Format varies by session: mock stakeholder interview, live Business Analysis Core Concept Model (BACCM) workshop, requirements conversion, solution challenge, or post-pilot retrospective.
- Closes with a stretch question that feeds into the next Session A share-out.
- Template: `Templates/Session_B_Template.md` | SME briefing: `Facilitator/Session_B_SME_Prep_Guide.md`

### The Case Study
One evolving TrailBlaze Adventures case study runs across all five sessions. Context is revealed progressively — participants only receive what is appropriate for the current session. The full story and all session-gated reveals are in `TrailBlaze_MasterContext.md` (facilitator only).

**Company background:** TrailBlaze Adventures is a mid-sized adventure travel company operating in the eastern United States, founded in 2018. The company runs guided trips ranging from half-day hikes to week-long expeditions. Its customer base centers on urban professionals and small family groups. Twelve full-time staff manage operations; approximately 40 guides work on a contracted, per-trip basis. Revenue splits roughly 60% from weekend trips and 40% from multi-day packages.

**The presenting symptom:** Weekend bookings declined 18% over two consecutive quarters. Leadership identified the problem but not the cause. Before a BA had been engaged, three competing diagnoses had already taken hold:

- **CEO:** The booking platform is outdated — a new customer-facing app will recover revenue.
- **Head of Operations:** Guide availability and scheduling are the real constraint.
- **Marketing Lead:** The brand is invisible to target demographics online.

The Finance Director has not offered a diagnosis. The technology budget is frozen pending a business case, which means no solution moves forward until the BA confirms what problem is actually being solved.

Each diagnosis has enough evidence behind it to sound credible. None has been confirmed. Session 1 begins the moment a BA is finally brought in — before any solution has been approved.

**The story arc:** Each session advances the engagement one stage and releases information participants did not have before. Session 2 delivers stakeholder interview data that reframes the problem — participants reconcile what they concluded in Session 1 with what the interviews show. Session 3 completes elicitation: scope is agreed, needs are surfaced, and constraints are on the table. By Session 4, three solution options are in play, the MVP feature set is locked, and Key Performance Indicators (KPIs) are confirmed. Session 5 brings pilot results: 30 days of live data, two missed targets, and traceable gaps in guide notification and Search Engine Optimization (SEO) that the BA had scoped but not prioritized.

The single-case design is deliberate. Real BA engagements do not reset every month — the BA inherits the last conversation, the last artifact, the last unanswered question. This series replicates that continuity. Participants build on their own prior work each session, which means their decisions compound. Session 1 teaches participants to write a problem statement with measurable criteria; that same statement gets stress-tested in Session 3 when they trace requirements back to it. A statement without criteria has nothing to trace to. The gap is visible, and closing it is the work.

Progressive reveal puts participants in the same position a BA occupies at first contact — a symptom, a set of stakeholders, and no confirmed cause. They make decisions with what they have. When Session 2 delivers interview data, participants return to their Session 1 problem statement with something at stake: they can see what they got right, what they assumed, and what they missed. That reflection is built into the design.

---

## TrailBlaze Adventures — Sequential Story Arc

| Session | Timing | TrailBlaze State | What participants receive |
|---------|--------|-----------------|---------------------------|
| **1A** | April | Bookings declining 18%. Leadership has conflicting diagnoses. No BA engaged yet. | Company brief + symptom only (OnePager_MicroExpeditions.md) |
| **1B** | Mid-April | CEO announces app to the board. Head of Operations signals guide attrition. BA not yet tasked. | New ambiguous prompt (screen only, Session 1 gate — no advance reveal) |
| **2A** | May | Leadership agrees to bring in a BA. Stakeholder interviews scheduled. Three competing root causes emerging. | Interview excerpts + competing root causes (TrailBlaze_MasterContext.md — Session 2 reveal) |
| **2B** | Mid-May | BA is in discovery. Stakeholders not yet aligned. Interview data incomplete. | Mock interview — SME plays a TrailBlaze stakeholder live; no new documents distributed |
| **3A** | June | BA has completed elicitation. Scope agreed: weekend booking + guide assignment workflow. Raw needs surfaced, not yet requirements. | Elicitation outputs + constraints (TrailBlaze_MasterContext.md — Session 3 reveal) |
| **3B** | Mid-June | Raw needs are on the table. Nothing has been verified or signed off yet. | Requirements conversion prompt — group works their own Session 3A outputs; no new reveal |
| **4A** | July | Three solution options proposed. MVP feature set agreed. NFRs and KPIs confirmed. | Solution options + MVP feature set + NFRs + KPIs (TrailBlaze_MasterContext.md — Session 4 reveal) |
| **4B** | Mid-July | Group has a solution recommendation. CEO has not yet approved it. | Solution challenge prompt — SME plays the CEO pushing back; no new reveal |
| **5A** | August | Pilot ran 30 days. Some targets met, some missed. Traced gaps in guide notification and SEO. | Pilot results with misses + lessons learned (TrailBlaze_MasterContext.md — Session 5 reveal) |
| **5B** | Mid-August | Pilot debrief underway. Improvement recommendations not yet finalized. | SME shares a real deployment miss; group maps it to TrailBlaze pilot data; no new reveal |

---

## ARCS Framework

**ARCS** stands for **Attention → Relevance → Confidence → Satisfaction**. It is a motivational design model developed by John Keller (1987) that structures the opening of each session to answer the learner's implicit questions: *Why should I pay attention? Why does this matter to me? Can I actually do this? Did it pay off?*

ARCS is a motivational sequence, not a fixed script — adapt the hook to the session topic.

| Element | What it does | Session 1 (cold open) | Sessions 2–5 (warm open) |
|---------|-------------|----------------------|-------------------------|
| **Attention** | Hook the group | Real-world failure story analogous to TrailBlaze's situation | Surprising or provocative question drawn from homework share-out |
| **Relevance** | Connect to what they care about | Direct tie to the TrailBlaze symptom | Link between what they just presented and the new session's concept |
| **Confidence** | Make them believe they can do it | Template walkthrough — shows the scaffold before the exercise | Acknowledge what the group already built; frame the new skill as a natural next step |
| **Satisfaction** | Give them a win | Share-out + facilitator feedback | Share-out + improved artifacts from homework |

**Session 1 flow:** Cold ARCS open (10 min) → concept instruction

**Sessions 2–5 flow:** Homework share-out (10–15 min) → ARCS bridge (3–5 min connecting what they presented to the new topic) → concept instruction

---

## Alignment Notes
- TrailBlaze context is revealed progressively — use `TrailBlaze_MasterContext.md` to know exactly what to share and when. Never give participants a reveal ahead of its session gate.
- ECBA exams test the 9 domains, not the BABOK KAs directly — these are related but not identical. Frame all exercises and debrief language through the domain lens.
- All session deliverables should use ECBA language (domains first, KA terminology as supporting context).
- Practice questions follow a 3-tier model: **checkpoint** (mid-concept, 1–2 Qs), **practice round** (end of session, timed Qs), **homework** (between sessions). All are ECBA exam-style multiple choice questions.
- Session B never advances the TrailBlaze story — it deepens what the group already has. If a prompt references future context, do not use it.
- The stretch question at the end of each Session B feeds directly into the next Session A share-out. Remind participants of this connection at the close of each Session B.

---

## Session Map

---

### Session 1 — Foundations & Core Concepts (April)

| | |
|---|---|
| **ECBA Domains** | Understanding Business Analysis, Mindset for Effective BA |
| **BABOK Coverage** | Introduction to BA, BACCM, BA mindset, values, principles, foundational competencies, assessing value (tangible vs. intangible, stakeholder-defined success) |
| **Required Reading** | BABOK Guide V3 — Ch. 1 (Introduction) + Ch. 2 (Key Concepts §2.1–2.4) |
| **TrailBlaze Reveal** | Company brief + symptom + conflicting leadership diagnoses (no root cause confirmed) |

#### Session A — 90 minutes
| Phase | Activity | Purpose | Time |
|-------|----------|---------|------|
| 1 — Open | ARCS cold open | Hook attention using an analogous failure; connect the TrailBlaze symptom to exam relevance; show the session scaffold | 10 min |
| 2 — Concepts | BA mindset and values, BACCM, foundational competencies, assessing value | Establish the vocabulary and frameworks participants apply immediately in phases 3–4 | 25 min |
| 3 — Guided application | BACCM class exercise: map TrailBlaze against all six elements | Model the analytical move before asking groups to execute it independently | 8 min |
| 4 — Group exercise | Stakeholder identification + problem statement with measurable criteria | First owned artifact; problem statement quality compounds through Sessions 2–4 traceability work | 25 min |
| 5 — Share-out | Group presentations + facilitator feedback | Calibrate the room; surface assumptions to address in Session 2 | 8 min |
| 6 — Practice round | 4 timed multiple choice questions | Immediate exam-pattern exposure while content is fresh | 8 min |
| 7 — Close | Homework assign + 2-min survey | Set expectations; collect baseline data on confidence and prior experience | 6 min |

**Checkpoints:** After BACCM slide / After Stakeholders slide

**Homework:** Refine and extend your in-session problem statement — add a value statement (one paragraph: what does solving this unlock for TrailBlaze?). Complete 6 exam multiple choice questions. Optional: persona exercise.

**Deliverables:** BACCM chart, stakeholder list, problem statement

#### Session B — 60 minutes (mid-April)
**Exercise:** Live BACCM workshop — SME plays themselves as "the BA who just walked into this company." Group works the BACCM against a new ambiguous TrailBlaze prompt with the SME pushing back on easy answers in real time.

**SME Profile:** Someone who has structured messy BA engagements from scratch (e.g., BA, project manager (PM), or consultant)

**Stretch Question:** *"How would you use the BACCM to push back on a solution that leadership has already decided on?"*

---

### Session 2 — Planning, Elicitation & Context (May)

| | |
|---|---|
| **ECBA Domains** | Implementing Business Analysis, Context |
| **BABOK Coverage** | BA Planning & Monitoring (Ch. 3): BA approach, stakeholder engagement, governance, information management, performance improvements — Elicitation & Collaboration (Ch. 4): prepare, conduct, confirm elicitation; communicate BA information; manage stakeholder collaboration — Implementing BA: roles, approaches, organizational factors, requirements vs. designs |
| **Required Reading** | BABOK Guide V3 — Ch. 3 (BA Planning & Monitoring) + Ch. 4 (Elicitation & Collaboration) |
| **TrailBlaze Reveal** | Stakeholder interview excerpts — three competing root causes; BA hired to define approach |

#### Session A — 90 minutes
| Phase | Activity | Purpose | Time |
|-------|----------|---------|------|
| 1 — Open | Homework share-out: problem statements + value statements | Surface quality variation; set up what the interview data reframes | 10 min |
| 2 — Bridge | ARCS reveal: interview data released; BA hired to define approach | Reframe Session 1 outputs — participants see whether their problem statement holds against stakeholder data | 5 min |
| 3 — Concepts | BA roles and approaches, organizational factors, requirements vs. designs, elicitation techniques, BA planning | Equip participants to make approach decisions under competing priorities, not follow a template | 25 min |
| 4 — Guided application | Map elicitation techniques to TrailBlaze stakeholder types; discuss approach selection under conflicting diagnoses | Model the judgment call; competing diagnoses have no single correct elicitation path | 10 min |
| 5 — Group exercise | Draft BA approach recommendation + stakeholder engagement plan | Owned artifact; feeds the mock stakeholder interview in Session B | 20 min |
| 6 — Share-out | Group presentations + facilitator feedback | Surface gaps in stakeholder coverage or approach logic before Session B | 8 min |
| 7 — Practice round | 4 timed multiple choice questions | Requirements vs. designs, BA approach selection, elicitation technique choice, organizational context | 8 min |
| 8 — Close | Homework assign + 2-min survey | — | 4 min |

**Checkpoints:** After BA roles + approaches + organizational factors / After Elicitation techniques

**Homework:** Starting from your in-session elicitation plan notes, draft a one-page BA approach recommendation: which approach, which stakeholders to engage first, and why. Complete 6 exam multiple choice questions.

**Deliverables:** BA approach recommendation, stakeholder engagement plan, elicitation plan for one stakeholder group

#### Session B — 60 minutes (mid-May)
**Exercise:** Mock stakeholder interview round — SME plays the Head of Operations or Marketing Lead, giving deliberately incomplete or conflicting answers. Group practices live elicitation. SME then steps out of character and debriefs on how real interviewees behave when they don't trust the BA.

**SME Profile:** Someone who has conducted or been subject to stakeholder interviews under pressure (e.g., BA, project sponsor, or functional manager)

**Stretch Question:** *"How do you document competing root causes without anchoring too early on one?"*

---

### Session 3 — Change, Need & Requirements Lifecycle (June)

| | |
|---|---|
| **ECBA Domains** | Change, Need |
| **BABOK Coverage** | Requirements Lifecycle Management (Ch. 6): trace, maintain, prioritize, assess changes, approve requirements — Strategy Analysis (Ch. 8): analyze current state, define future state, assess risk, define change strategy |
| **Required Reading** | BABOK Guide V3 — Ch. 6 (Requirements Lifecycle Management) + Ch. 8 (Strategy Analysis) |
| **TrailBlaze Reveal** | Elicitation outputs — raw needs (unconverted), scope agreed, constraints confirmed |

#### Session A — 90 minutes
| Phase | Activity | Purpose | Time |
|-------|----------|---------|------|
| 1 — Open | Homework share-out: BA approach docs + elicitation plans | Validate or challenge approach choices before moving to requirements work | 10 min |
| 2 — Bridge | ARCS reveal: elicitation outputs released — raw needs, agreed scope, constraints | Reframe: participants have data — what counts as a requirement, and what stays a need? | 5 min |
| 3 — Concepts | Current state vs. future state, risk assessment, change strategy; requirements lifecycle — trace, maintain, prioritize, assess changes | Establish the framework that determines whether a requirement survives review | 22 min |
| 4 — Guided application | Current-state and future-state framing using TrailBlaze interview data | Show how the same data produces different state pictures depending on framing choices | 8 min |
| 5 — Group exercise | Root cause analysis + convert 3 raw needs to written requirements using lifecycle criteria | Core artifact; requirement quality here determines what Session 4 traceability work looks like | 22 min |
| 6 — Share-out | Group presentations + facilitator feedback; flag vague language as fuel for Session B | Surface requirements that will not survive scrutiny before the conversion workshop | 8 min |
| 7 — Practice round | 4 timed multiple choice questions | Traceability, prioritization, change strategy, need vs. solution | 8 min |
| 8 — Close | Homework assign + 2-min survey | — | 7 min |

**Checkpoints:** After current-state / future-state framing / After requirements lifecycle concepts

**Homework:** Starting from your in-session raw needs list, convert 3 of them into written requirements using proper BA language. Complete 6 exam multiple choice questions.

**Deliverables:** Current-state summary, root cause analysis, requirements converted from raw needs, change strategy draft

#### Session B — 60 minutes (mid-June)
**Exercise:** Requirements conversion workshop — group brings their raw needs; SME participates as a senior BA would, challenging vague language, flagging scope creep, asking "how would you verify this?" Focus: what gets lost in translation from raw need to written requirement.

**SME Profile:** Someone who has written or reviewed requirements on a real project (e.g., BA, systems analyst, or product owner)

**Stretch Question:** *"How do you get sign-off from a stakeholder who doesn't fully understand the requirements they're approving?"*

---

### Session 4 — Solution, Stakeholder & Requirements Analysis (July)

| | |
|---|---|
| **ECBA Domains** | Solution, Stakeholder |
| **BABOK Coverage** | Requirements Analysis & Design Definition — RADD (Ch. 7): specify and model, verify, validate, architecture, design options, recommend solution — Solution Evaluation (Ch. 9): measure performance, assess limitations, recommend improvements |
| **Required Reading** | BABOK Guide V3 — Ch. 7 (RADD) + Ch. 9 (Solution Evaluation) |
| **TrailBlaze Reveal** | Three solution options, MVP feature set, NFRs, KPIs |

#### Session A — 90 minutes
| Phase | Activity | Purpose | Time |
|-------|----------|---------|------|
| 1 — Open | Homework share-out: converted requirement sets | Surface quality; identify which requirements are strong enough to trace to a solution | 10 min |
| 2 — Bridge | ARCS reveal: three solution options, MVP feature set, NFRs, KPIs released | Reframe: from "what do we need?" to "which path solves it, and how do we prove it?" | 5 min |
| 3 — Concepts | RADD — specify and model, verify, validate, design options, solution recommendation; solution evaluation — measure performance, assess limitations, recommend improvements | Equip participants to recommend a solution they can defend on traceability grounds | 23 min |
| 4 — Guided application | Walk one TrailBlaze requirement through the full RADD process; distinguish requirements from designs | Requirements and designs are not the same — a persistent exam failure point | 10 min |
| 5 — Group exercise | Solution options analysis + RTM stub linking requirements to the recommended option | Owned artifact; connects requirement work from Sessions 1–3 to a defensible recommendation | 20 min |
| 6 — Share-out | Group presentations + facilitator feedback; challenge any recommendation unsupported by the RTM | Surface reasoning gaps before the Session B CEO challenge | 8 min |
| 7 — Practice round | 4 timed multiple choice questions | Solution recommendation, requirements validation, RTM, stakeholder engagement in solution phase | 8 min |
| 8 — Close | Homework assign + 2-min survey | — | 6 min |

**Checkpoints:** After RADD specify-and-model / After solution evaluation concepts

**Homework:** Starting from your in-session solution options table, write a one-paragraph recommendation with rationale. Link at least 3 requirements to your recommended option in an RTM stub. Complete 6 exam multiple choice questions.

**Deliverables:** Stakeholder map, solution options analysis with recommendation, RTM draft

#### Session B — 60 minutes (mid-July)
**Exercise:** Solution challenge — group presents their recommendation; SME plays the CEO or a real executive analog, pushing back with genuine objections (cost, political reality, timeline, "we already tried that"). Group defends using ECBA language. SME then debriefs on how solution decisions actually get made.

**SME Profile:** Someone who has presented solution options to executive sponsors or been a decision-maker (e.g., manager, director, or former exec)

**Stretch Question:** *"How do you trace a requirement back to a solution option when the options change late in the process?"*

---

### Session 5 — Value, Review & Exam Readiness (August)

| | |
|---|---|
| **ECBA Domains** | Value + integrated review of all 9 domains |
| **BABOK Coverage** | Full review of all 6 KAs — no new content; consolidation and exam pattern recognition |
| **Required Reading** | BABOK Guide V3 — Ch. 10 (Techniques reference) + review all personal notes and homework multiple choice questions from Sessions 1–4 |
| **TrailBlaze Reveal** | Pilot results — some targets missed, gaps traced to guide notification and SEO |

#### Session A — 90 minutes
| Phase | Activity | Purpose | Time |
|-------|----------|---------|------|
| 1 — Open | Homework share-out: solution recommendations + RTM drafts | Surface final artifacts; create stakes before the pilot data arrives | 8 min |
| 2 — Reveal | ARCS pilot data reveal: 87/100 bookings, two missed KPI targets, traceable gaps in guide notification and SEO | Reframe: the BA scoped this — what was prioritized, what was not, and what did that cost? | 7 min |
| 3 — Concepts | Value domain: measuring BA outcomes, tangible vs. intangible value, BA effectiveness and performance improvement | Ground the post-pilot analysis in ECBA language before participants apply it | 15 min |
| 4 — Post-pilot analysis | Map pilot results against KPIs; trace missed targets back to requirements; identify sequencing and traceability errors | Apply all five sessions of accumulated work to a real outcome; evidence required, no single right answer | 18 min |
| 5 — Extended practice round | 8–10 timed multiple choice questions across all 9 domains | Exam simulation: integrated scenario questions, not topic-specific | 20 min |
| 6 — Quiz game | Kahoot- or Jeopardy-style team round — 3–5 questions per domain | Lower-stakes calibration; surfaces honest gaps that individual practice hides | 12 min |
| 7 — Q&A + exam prep | Open Q&A + facilitator walks through exam prep plan | Named concerns addressed; participants leave with a concrete study schedule | 8 min |
| 8 — Close | 2-min survey | — | 2 min |

**Quiz Game:** Kahoot-style or Jeopardy-style team round — categories map to the 9 ECBA domains; 3–5 questions per domain; facilitator uses incorrect answers as teaching moments

**Deliverables:** KPI analysis, improvement recommendations, full exam scenario practice set

#### Session B — 60 minutes (mid-August)
**Exercise:** Post-pilot retrospective — SME shares a real story of a deployment where some targets were hit and others missed. Group maps the SME's story against the TrailBlaze pilot data. Closes with SME reflecting on which ECBA concept mattered most in their career and why.

**SME Profile:** Someone who has been through a post-deployment evaluation or lessons-learned process (e.g., BA, PM, or operations manager)

**Stretch Question:** *"Looking back on a real project, what is one ECBA concept you wish you had understood better before starting?"*

---

## Abbreviations

| Abbreviation | Meaning |
|---|---|
| **ARCS** | Attention, Relevance, Confidence, Satisfaction — Keller's motivational design model |
| **BA** | Business Analyst / Business Analysis |
| **BABOK** | Business Analysis Body of Knowledge (IIBA, V3) |
| **BACCM** | Business Analysis Core Concept Model |
| **ECBA** | Entry Certificate in Business Analysis |
| **IIBA** | International Institute of Business Analysis |
| **KA** | Knowledge Area (BABOK term) |
| **KPI** | Key Performance Indicator |
| **MVP** | Minimum Viable Product |
| **NFR** | Non-Functional Requirement |
| **RADD** | Requirements Analysis and Design Definition (BABOK Ch. 7) |
| **RTM** | Requirements Traceability Matrix |
| **SME** | Subject Matter Expert |
