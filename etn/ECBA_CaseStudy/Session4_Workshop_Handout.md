# Session 4 — Workshop Handout
## Solution, Stakeholder & Requirements Analysis
ECBA Domains: Solution | Stakeholder
Duration: 90 minutes

--- DOCUMENT GUIDE ---
What this is:   Participant exercise sheet for Session 4A.
Who it's for:   Every participant in Session 4A.
When to use it: Distribute at the ARCS bridge, just before Exercise 1, after releasing the solution options and MVP details.
--- END GUIDE ---

---

**Where we are in the TrailBlaze story:**
The BA has completed elicitation. Three solution options have been proposed. The MVP feature set has been agreed. NFRs and KPIs are confirmed. Your job this session is to evaluate the options, recommend one, and build the start of a Requirements Traceability Matrix (RTM) that connects your recommendation back to the requirements you wrote in Session 3.

**The three solution options:**

**Option 1 — Enhance the existing website with a self-serve booking flow**
Add a booking layer on top of the existing website: trip calendar, booking form, payment processing, automated confirmation email, and ops dashboard. No mobile app. Guide assignment notification integrated into the ops dashboard.
- Estimated cost: $28,000–$35,000
- Estimated build time: 8 weeks
- Vendor dependency: payment gateway integration (Stripe); no new platform vendor

**Option 2 — Build a new mobile-first booking platform with guide matching**
Full rebuild of the web presence plus a native mobile app for customers. Includes automated guide matching based on availability data, a guide-facing mobile app for assignments and rosters, and customer profile management for repeat bookings.
- Estimated cost: $85,000–$110,000
- Estimated build time: 14–18 weeks (exceeds the 10-week MVP constraint)
- Note: This exceeds both the budget and the build timeline agreed with Patricia. A phased approach would be needed.

**Option 3 — Partner with an existing outdoor booking marketplace**
List TrailBlaze trips on an established outdoor adventure marketplace (e.g., GetYourGuide, Viator, or a niche outdoor platform). No custom build. Customer bookings flow through the marketplace; TrailBlaze operations receive a booking notification.
- Estimated cost: $0 build cost; revenue share 15–20% of booking value per transaction
- Implementation time: 2–4 weeks for onboarding and listing setup
- Constraint: no control over the customer experience or guide workflow; guide notification still happens through the current process

**NFRs confirmed (all options must meet):**
- Booking service availability: 99.5% during peak hours (7am–11pm ET)
- Search and filter response time: results in under 500ms at 95th percentile load
- Payment processing: PCI-compliant; customer card data not stored in TrailBlaze systems
- Concurrent booking support: at least 200 simultaneous active sessions during pilot

**KPIs agreed for the pilot (30-day window):**
- 100 pilot bookings (new bookings through the new process)
- NPS of 8.0 or higher
- On-time departure rate of 95% or higher
- Payment success rate of 99% or higher
- Guide assignment confirmed at least 24 hours before trip start

**Reference materials for this session:**
- Session3_ElicitationOutputs.md — the requirements you converted last session
- Stakeholders_Detailed.md — the full stakeholder analysis (distribute this session)
- RTM_Sample.md — the RTM starting structure
- Your own Session 3 homework (bring your written requirements)

**Group setup:** Groups of 3–4. Assign a scribe and a presenter.

---

## Exercise 1 — Solution Options Analysis (12 minutes)

Evaluate all three options against the requirements and constraints. Use the table below.

| Criterion | Option 1 (Website Enhancement) | Option 2 (Mobile Platform) | Option 3 (Marketplace) |
|-----------|-------------------------------|---------------------------|----------------------|
| Meets 10-week build timeline? | | | |
| Within budget (conditional approval)? | | | |
| Addresses customer booking need? | | | |
| Addresses guide assignment/notification need? | | | |
| Gives Jordan the conversion data she needs? | | | |
| Gives Patricia the ROI visibility she requires? | | | |
| Gives Sam and guides improved notification? | | | |
| Creates long-term platform capability TrailBlaze owns? | | | |

**Note:** You may find that no option satisfies every criterion fully. That is normal — and it is important information. A BA's job is not to find a perfect option; it is to make a defensible recommendation based on the evidence.

---

## Exercise 2 — RTM Starter (20 minutes)

Select your recommended option. Build an RTM that traces your recommendation back to the requirements.

**Structure of an RTM row:**

| Business Goal | Requirement | Feature / User Story | Acceptance Criteria | Owner | Option Satisfied |
|---|---|---|---|---|---|

**Business goals for TrailBlaze (use these):**
- Increase pilot weekend bookings to 100 in first 30 days
- Improve on-time departure rate to 95% or higher
- Deliver NPS of 8.0 or higher
- Enable operations to manage bookings without manual email/Google Sheet process
- Ensure guides receive assignments with required information and lead time

**Your task:**
1. Take your 3 written requirements from Session 3 homework
2. Map each requirement to the business goal it supports
3. Identify which feature or user story satisfies it (use the MVP feature list from Session3_ElicitationOutputs.md)
4. Write acceptance criteria — the specific, testable condition that confirms the requirement is met
5. Name the owner (who is responsible for this requirement being delivered)

**You should have at least 3 rows.** You may add more.

---

## Exercise 3 — Solution Recommendation (8 minutes)

Write a one-paragraph recommendation. It must include:
- Which option you recommend and the primary reason
- Which requirement(s) drove your decision
- The most significant risk of your recommended option
- What you would do if that risk materializes

**What a weak recommendation looks like:**
*"We recommend Option 1 because it is faster and cheaper and addresses the main booking problem."*
— No requirement cited. Risk not named. Nothing to trace back.

**What a stronger recommendation looks like:**
*"We recommend Option 1 (website enhancement) because it is the only option that satisfies the 10-week build timeline and the conditional budget approval, while also delivering the guide notification workflow (see requirement [#], Session 3). The primary risk is that Option 1 does not natively support mobile — our persona data suggests Alex books on mobile, and a poor mobile experience may limit pilot conversion rates. If mobile performance falls below usable thresholds during QA, we recommend adding responsive design as a sprint priority before launch rather than delaying the pilot."*
— Requirement cited. Risk named. Response to risk stated.

---

## Share-out (3–4 minutes per group)

Present:
- Your recommendation in one sentence
- The one requirement that most influenced your choice (and why)
- The one risk you named and your response to it

---

## Rubric (12 pts)

- **Solution analysis (0–3):** Table completed; constraints applied honestly (no option gets full marks for everything); reasoning visible in completed cells
- **RTM (0–3):** Requirements from Session 3 homework used; acceptance criteria are testable; owners named (not just "everyone")
- **Recommendation (0–3):** Option named with a reason; requirement cited; risk named and response given
- **Presentation clarity (0–3):** Recommendation is one paragraph; language is professional; framing is BA-language (traceability, risk, stakeholder impact) not personal preference

---

## Homework (due before Session 5)

**Individual — Written Artifact:**
Starting from your in-session solution analysis, write a one-paragraph recommendation (same format as Exercise 3 above — refine your in-session version if you have one). Then add:
- An RTM stub linking at least 3 requirements from Session 3 homework to your recommended option
- One sentence per row describing the acceptance criterion

**Individual — Practice Questions:**
Complete Session4_PracticeQuestions.md — Homework 1 through 6.

**Required reading before Session 5:**
- BABOK Guide V3 — Chapter 10: Techniques (review; focus on gap analysis, decision analysis, and risk analysis)
- Review all personal notes and homework MCQs from Sessions 1–4
- Bring your complete artifact set: problem statement, BA approach, requirements set, RTM stub, and recommendation

**Optional group:**
Share your RTM stubs. For each requirement-to-acceptance-criteria link: *"Can I write a test case that would fail this? Is the acceptance criterion tight enough to catch a bad implementation?"*
