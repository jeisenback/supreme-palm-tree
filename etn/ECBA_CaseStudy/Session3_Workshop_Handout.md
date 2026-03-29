---
content_type: ecba_session
session_id: 3
slot: handout
status: published
---

# Session 3 — Workshop Handout
## Change, Need & Requirements Lifecycle
ECBA Domains: Change | Need
Duration: 90 minutes

--- DOCUMENT GUIDE ---
What this is:   Participant exercise sheet for Session 3A.
Who it's for:   Every participant in Session 3A.
When to use it: Distribute at the ARCS bridge, just before Exercise 1, after releasing the elicitation outputs.
--- END GUIDE ---

---

**Where we are in the TrailBlaze story:**
The BA has completed stakeholder interviews and two workshops. Scope has been agreed. You just received the raw outputs from those activities — a mix of sticky notes, a process walkthrough, and a list of raw needs. Your job this session is to work with that material: define the current state and future state, and convert the messiest raw needs into something a developer could actually build to.

**Reference materials for this session:**
- Session3_ElicitationOutputs.md — the elicitation outputs you just received
- Session2_StakeholderInterviews.md — the interviews from Session 2 (for context)
- OnePager_MicroExpeditions.md — company background

**Group setup:** Groups of 3–4. Assign a scribe and a presenter.

---

## Exercise 1 — Current State and Future State (15 minutes)

**Part A: Current state summary (7 minutes)**

Using the process walkthrough table from the elicitation outputs, write a current state summary for the TrailBlaze booking process. A current state summary answers:
- What is the process doing right now?
- Where is it breaking down?
- What is the measurable impact of those breakdowns?

Keep it to 3–5 bullet points. Be specific — "the process is slow" is not a current state summary. "A standard booking takes 45–90 minutes of staff time across 3–5 days" is.

**Part B: Future state description (8 minutes)**

Based on the agreed scope and raw needs, write a future state description. A future state description answers:
- What should the process look like when the MVP is working?
- Who does what differently?
- What is the measurable outcome that tells you the future state has been reached?

Keep it to 3–5 bullet points. The future state should connect directly to the KPIs (if you don't remember them from Session 1, check the OnePager).

**Tip:** The gap between your current state and future state is what you are scoping. If your future state is vague, your requirements will be vague.

---

## Exercise 2 — Root Cause Verification (10 minutes)

In Session 2, you identified three competing root causes. You now have more data (process walkthrough, workshop sticky notes). Use that data to answer these three questions:

1. **Which root cause is now most strongly supported by evidence?** What specific evidence from the elicitation outputs confirms it?
2. **Which root cause has the least direct evidence?** What would you still need to confirm it?
3. **Are the root causes independent, or does fixing one likely fix the others?**

Write 2–3 sentences for each question. This is a thinking exercise, not a fill-in-the-blank.

---

## Exercise 3 — Requirements Conversion (20 minutes)

**This is the core exercise of Session 3.**

Below are 4 raw needs from the elicitation outputs. Your job is to convert 3 of them into written requirements.

A written requirement is:
- **Specific** — leaves no room for two people to interpret it differently
- **Verifiable** — you can write a test that confirms it is or isn't met
- **Solution-agnostic** — it describes what must be true, not how to make it true
- **Owned by a stakeholder** — you can name who needs this and why

**A worked example (not from TrailBlaze):**

| | Example |
|---|---|
| **Raw need** | "The form needs to be easy to fill out on a phone" |
| **Bad requirement** | "The booking form should be mobile-friendly" — *not specific, not verifiable* |
| **Better requirement** | "All required booking form fields must be accessible and submittable on a mobile browser (iOS Safari, Android Chrome) without horizontal scrolling at a viewport width of 375px or above" |
| **Why it's better** | Specific enough to test. Clear what passes and fails. Doesn't dictate the design — just the constraint. |

**The 4 raw needs — convert any 3:**

| # | Raw Need | Your Written Requirement |
|---|----------|-------------------------|
| 1 | "Guides need to receive assignment confirmation with sufficient lead time" | |
| 2 | "Customers want to know the guide's qualifications before they book" | |
| 3 | "Operations needs to be notified when a booking is made" | |
| 4 | "Liability waivers must be collected and stored before the trip" | |

**After writing each requirement, answer:**
- How would you verify this requirement is met? (1 sentence)
- What assumption did you have to make to write it? (1 sentence)

---

## Share-out (3–4 minutes per group)

Present:
- Your future state description (summarized to 2–3 key points)
- One written requirement — read it aloud, then answer: "How would you verify this?"

---

## Rubric (12 pts)

- **Current/future state (0–3):** Current state is specific and measurable; future state connects to KPIs; gap between them is visible
- **Root cause verification (0–3):** Evidence cited from the elicitation outputs; at least one cause named as unconfirmed; relationship between causes addressed
- **Requirements conversion (0–3):** Requirements are specific, verifiable, and solution-agnostic; at least one assumption stated; verification method named
- **Presentation clarity (0–3):** Future state described without using solution language; requirements read as constraints, not designs

---

## Homework (due before Session 4)

**Individual — Written Artifact:**
Starting from your in-session raw needs list, convert 3 raw needs into written requirements — these can be the same 3 you worked on in the session, refined, or 3 different ones. For each requirement:
- Write the requirement in one or two sentences
- Name the stakeholder who owns this need
- Describe how you would verify it is met
- Identify one assumption you made in writing it

**Individual — Practice Questions:**
Complete Session3_PracticeQuestions.md — Homework 1 through 6.

**Required reading before Session 4:**
- BABOK Guide V3 — Chapter 7: Requirements Analysis and Design Definition (RADD)
- BABOK Guide V3 — Chapter 9: Solution Evaluation
- Focus on: specify and model requirements, verify and validate requirements, define design options, analyze potential value, recommend solutions, measure performance

**Optional group:**
Share your requirements in the group channel. For each requirement someone else wrote: *"Can I break this? Is there a way to interpret this requirement that allows a solution that doesn't actually solve the problem?"* Requirements that survive this question are strong.