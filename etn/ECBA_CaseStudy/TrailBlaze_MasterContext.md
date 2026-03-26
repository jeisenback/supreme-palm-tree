TrailBlaze Adventures — Master Context (Facilitator Only)

--- DOCUMENT GUIDE ---
What this is:   Full TrailBlaze Adventures story with all 5 session-gated reveals — company background, competing root causes, stakeholder detail, solution options, and pilot results.
Who it's for:   Facilitator only.
When to use it: Review before each session to confirm exactly what context to release and when.
Restricted:     Yes — never share this document with participants at any stage.
--- END GUIDE ---

---

COMPANY BACKGROUND (available any session)

TrailBlaze Adventures is a guided outdoor adventure company based in Asheville, NC, founded in 2018 by Marcus Webb. They offer guided trips from half-day hikes to week-long expeditions, primarily serving urban professionals and small family groups. Revenue splits roughly 60% weekend trips, 40% multi-day packages. 12 full-time staff, ~40 contracted guides (seasonal, per-trip). No online booking — customers call or email to book. The full operational detail is in OnePager_MicroExpeditions.md.

Key people (names consistent across all documents):
- CEO and Founder: Marcus Webb
- Head of Operations: Rachel Okonkwo
- Marketing Lead: Jordan Ash
- Finance Director: Patricia Chu
- Lead Guide Representative: Sam Torres
- Operations Coordinator (front-line): Keisha Daniels

---

SESSION 1 REVEAL — Company brief + symptom only
(What participants receive: OnePager_MicroExpeditions.md and Session1_Workshop_Handout.md)

- Weekend bookings declined 18% over two consecutive quarters (from ~65/month peak to ~53/month)
- Marcus Webb (CEO) believes the solution is a new booking platform; has already had a FareHarbor demo without notifying the team
- Rachel Okonkwo (Head of Operations) believes the real issue is guide availability and scheduling — turn-away rate is real but not formally tracked
- Jordan Ash (Marketing Lead) believes it is a brand awareness and search discoverability problem
- Patricia Chu (Finance Director) has frozen the technology budget pending a formal business case
- Sam Torres (Lead Guide Rep) is not yet named in the Session 1 materials — participants may or may not identify him as a stakeholder
- Keisha Daniels (Operations Coordinator) handles all front-line booking contacts — her role in the process is described in the OnePager
- No BA has been engaged yet

Facilitator note: Do not confirm which diagnosis is correct. Participants must define the need before any solution is valid. Marcus's FareHarbor demo is a real detail — surface it only if participants ask "has leadership already done anything?" or when it becomes relevant.

---

SESSION 2 REVEAL — BA engagement begins; interview transcripts released
(Full participant document: Session2_StakeholderInterviews.md — distribute at the ARCS bridge)

The full interview transcripts are in Session2_StakeholderInterviews.md. Key signals for the facilitator:

Marcus Webb:
- Attributes the decline to the booking platform (no direct data; reasoning is "obvious explanation")
- Has frozen the diagnosis around a solution he already prefers
- Has not connected guide attrition to the booking decline
- Will tell the BA what they want to hear and then proceed with the app anyway

Rachel Okonkwo:
- Confirms a real turn-away problem: 1–2 bookings/month lost due to guide confirmation delays (~2–4% of peak volume)
- Guide pool has experienced turnover; newer guides need more lead time than experienced ones
- Won't say directly that she's worried about her job if the process is automated
- Has 30+ improvement ideas she's never had time to implement
- Will give you everything if you ask specific questions and show you've done your homework

Jordan Ash:
- Has real data on the SEO problem (basic keyword research showing competitor outranking TrailBlaze)
- Cannot prove marketing ROI because there is no website analytics tracking
- Has been requesting a website redesign for 8 months without a formal response
- Minimizes her frustrations; "I've been thinking about whether..." = "I've been fighting for this"

Patricia Chu:
- Has already run her own rough numbers on the booking decline and the ROI of a platform
- Will share her analysis only after the BA has done theirs independently
- Has a clear framework for what a business case must include
- Is aware of guide turnover and its impact — she is the only leadership stakeholder who names it unprompted

Sam Torres:
- Confirms the assignment notification problem with a specific incident (allergy not communicated; cardiovascular condition discovered at trailhead)
- Names guide turnover as partly caused by the notification and communication failures
- Has never been asked for input before this interview
- Distinguishes clearly between the customer booking problem (not his) and the guide assignment problem (his)

Key insight for facilitator: Three root causes are visible in the interviews — inquiry drop-off (Marcus's framing), guide availability and notification failures (Rachel and Sam's framing), and search discoverability (Jordan's framing). Patricia is the only stakeholder who holds all three simultaneously. Participants who read only Marcus's interview will anchor on the platform. Participants who read all five and compare will see the fuller picture.

---

SESSION 3 REVEAL — Elicitation outputs, scope agreement, and raw needs
(Full participant document: Session3_ElicitationOutputs.md — distribute at the ARCS bridge)

The full elicitation outputs are in Session3_ElicitationOutputs.md. Summary for the facilitator:

- Agreed scope: weekend trip booking experience (customer-facing) + guide assignment and notification workflow (internal)
- Out of scope (post-MVP): multi-day packages, guide payment, rental gear inventory, group discounts
- Build team: 1 FE, 1 BE, 0.5 QA, 0.5 BA/PM — no dedicated PM; BA is de facto product owner
- Budget: conditionally unfrozen; business case must be signed before sprint 3
- The Session 3 document includes: raw sticky note outputs (intentionally unsorted), process walkthrough table (Keisha's current booking process step by step), scope agreement summary, and a raw needs list
- Guide contracts are seasonal; availability cannot be pulled automatically — Rachel or a delegate must maintain it manually

Key exercise for facilitator to watch: participants converting raw needs to written requirements. The most common errors are: (1) writing solutions instead of requirements ("the system shall send a text message" vs. "guides must receive assignment confirmation with at least 72 hours' notice"), (2) writing requirements that cannot be tested ("the booking experience should be intuitive"), and (3) not naming a stakeholder owner. The worked example in Session3_Workshop_Handout.md shows the difference explicitly.

---

SESSION 4 REVEAL — Solution options + RTM
(Use for solution evaluation and traceability exercises)

- Three solution options have been proposed for stakeholder review:
  1. Enhance the existing website with a self-serve booking flow (low cost, 8 weeks)
  2. Build a new mobile-first booking platform with guide matching (higher cost, 14 weeks)
  3. Partner with an existing outdoor booking marketplace (no build, revenue share model)
- MVP feature set agreed after workshop (participants build RTM from this):
  - Browse and filter trips by date, difficulty, location
  - Bookable trip checkout with payment and confirmation email
  - Guide assignment dashboard (internal ops)
  - Customer itinerary PDF delivery
  - Pilot NPS survey
- NFRs confirmed:
  - Booking service availability: 99.5% during peak hours
  - Search performance: results < 500ms at 95th percentile
  - PCI-compliant payment flow; customer data encrypted at rest
  - Support 200 concurrent booking sessions during pilot
- KPIs agreed:
  - Booking conversion rate
  - 100 pilot bookings in first 30 days
  - NPS ≥ 8
  - On-time departure rate ≥ 95%
  - Payment success rate ≥ 99%
  - Guide assignment confirmed < 24 hours before trip

---

SESSION 5 REVEAL — Pilot results + lessons learned
(Use for BA effectiveness and continuous improvement exercises)

- Pilot ran for 30 days following MVP launch
- Results:
  - 87 bookings (target: 100) — missed by 13%
  - NPS: 8.2 (target met)
  - On-time departure rate: 91% (target: 95% — missed)
  - Payment success rate: 99.4% (target met)
  - Guide assignment < 24 hours: 78% (target not formally measured — gap identified)
- Root cause of missed targets:
  - Bookings short: search SEO not optimised at launch; marketing campaign delayed 2 weeks
  - Departure rate: ops dashboard did not surface same-day changes; guides missed updates
- Stakeholder satisfaction scores (BA effectiveness measurement):
  - CEO: 4/5 — "Good progress but we need to move faster on mobile"
  - Head of Ops: 3/5 — "Dashboard helped but guide comms still broke down"
  - Marketing Lead: 5/5 — "Finally have a platform we can promote"
  - Finance Director: 4/5 — "ROI trajectory is positive, want quarterly reviews"
- Lessons learned (participants identify gaps in BA approach and recommend next steps):
  - Guide notification workflow was elicited but not prioritised — sequencing error
  - SEO requirements were in scope but not traced to any sprint — traceability gap
  - Recommend: post-pilot BA retrospective, updated RTM, refined ops workflow requirements
