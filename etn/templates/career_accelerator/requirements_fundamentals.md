---
content_type: career_accelerator
subtype: requirements_fundamentals
slot: facilitator_guide
status: template
---

# Requirements Fundamentals — Facilitator Guide

## Session Overview

**Format:** Concept + practice workshop (90 min)
**Audience:** Career changers and early-career BAs with limited formal BA training
**Goal:** Participants can distinguish requirement types, write testable requirements, and understand how requirements connect to delivery.

## Learning Objectives

By the end of this session, participants will be able to:
- Distinguish business, stakeholder, solution, and transition requirements
- Apply SMART criteria to evaluate requirement quality
- Trace a requirement from business need to test case

## Materials

- [ ] Requirements worksheet (participant_handout.md)
- [ ] "Good vs. bad requirements" card sort (15 cards)
- [ ] RTM starter template (1 per participant)
- [ ] Case company one-pager (reuse from Case Workshop or create standalone)

## Agenda

| Time | Segment | Notes |
|------|---------|-------|
| 0:00 | Welcome + why requirements fail | 10 min |
| 0:10 | Requirement types: the four layers | 15 min |
| 0:25 | Card sort activity: classify and fix bad requirements | 20 min |
| 0:45 | Writing testable requirements (SMART + conditions of satisfaction) | 15 min |
| 1:00 | Traceability: connecting needs to tests | 15 min |
| 1:15 | Wrap-up + take-home practice | 5 min |

## Facilitation Notes

### Why Requirements Fail (10 min)
[FACILITATOR: Open with a brief war story about requirements failure — gold-plating, scope creep, or the team that built the wrong thing perfectly. The point: vague requirements are expensive.]

Key stat to share: Standish Group CHAOS reports consistently find poor requirements as a top project failure driver.

### The Four Layers (15 min)
[FACILITATOR: Use the pyramid metaphor: Business Requirement (why) → Stakeholder Requirement (who needs what) → Solution Requirement (functional + non-functional) → Transition Requirement (how we get there).]

Common confusion: mixing solution and stakeholder requirements. "The system shall..." vs. "The user needs to..." — these are different levels and mixing them causes traceability gaps.

### Card Sort Activity (20 min)
[FACILITATOR: Give groups a set of 15 requirement statements. Tasks:
1. Classify each by type (business/stakeholder/solution/transition)
2. Identify which are NOT testable and why
3. Rewrite 2 bad requirements using SMART criteria

Common fixes to model:
- Remove ambiguity ("user-friendly" → "task completion under 90 seconds for trained users")
- Add measurability ("fast" → "response time < 500ms at peak load")
- Specify conditions ("the system shall notify users" → "the system shall send an email notification within 5 minutes of...")
]

### Testable Requirements (15 min)
[FACILITATOR: Introduce conditions of satisfaction: Given [context], When [action], Then [observable outcome]. This is pre-BDD thinking that translates directly to test cases.]

Exercise: Have participants write one acceptance criterion for a requirement they work with daily.

### Traceability (15 min)
[FACILITATOR: Walk through a minimal RTM: Business Need → Stakeholder Req → Solution Req → Test Case. The point is not the tool (Excel, Jira, whatever) — the point is the link. If a requirement can't be traced back to a business need, it may be gold-plating.]

## Debrief Questions

- Which requirement type do you encounter most in your work? Which least?
- What makes a requirement "good enough" vs. perfect?
- Where does traceability break down on your current projects?

## Pre-Work (assign 1 week before)

See `pre_work.md`. Ask participants to bring one real requirement from their work (anonymized if needed).

## Resources

- BABOK v3 Chapter 6: Requirements Analysis and Design Definition
- IEEE 830 requirements quality checklist (simplified version)
- ETN RTM template (Excel)
