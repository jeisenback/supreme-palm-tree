---
content_type: ecba_session
label: case_study
session_id: 3
slot: handout
status: published
---

# TrailBlaze Adventures — Elicitation Outputs (Session 3)

--- DOCUMENT GUIDE ---
What this is:   Raw outputs from the BA's elicitation activities — two stakeholder workshops and a process walkthrough with Keisha. This is what the BA produced before structuring began. It is intentionally messy.
Who it's for:   Participants (Session 3 reveal).
When to use it: Release at the ARCS bridge in Session 3A. Participants use these outputs to convert raw needs into written requirements in the group exercise.
Facilitator note: The raw sticky note section is intentionally unorganized. Do not pre-sort it for participants. Sorting the signal from the noise is part of the exercise.
--- END GUIDE ---

---

## What happened between Session 2 and now

The BA conducted two workshops (one with operations, one with the broader leadership team) and a process walkthrough with Keisha to document the current booking workflow end to end.

Scope was negotiated and agreed:
- **In scope:** Weekend trip booking experience (customer-facing) + guide assignment and notification workflow (internal operations)
- **Out of scope:** Multi-day expedition packages (too complex for MVP), guide payment processing (separate workstream), legal and permit infrastructure (ongoing)

The financial constraint has shifted: Patricia has agreed to a 10-week MVP build contingent on formal business case sign-off. The technology budget is conditionally unfrozen.

Team available for the build:
- 1 frontend developer (Sarah, full-time, works remotely)
- 1 backend developer (David, full-time, on-site)
- 1 QA tester (Priya, part-time, 3 days/week)
- 0.5 BA / product (you, shared with other engagements)

**There is no dedicated project manager. The BA is also the de facto product owner for this engagement.**

---

## Part 1 — Raw Sticky Note Outputs

*From Workshop 1 (Operations team: Rachel, Keisha, Sam on video) and Workshop 2 (Leadership: Marcus, Rachel, Jordan, Patricia)*

*These are verbatim transcriptions of sticky notes from the Miro board. They have not been sorted, combined, or edited. They are in the order they were placed on the board.*

---

- "Customers should be able to book without calling us"
- "Need to know if a guide has first aid training before I sign off" — Patricia
- "Guides need more than 48 hours notice!!" — Sam (via video)
- "The Google Sheet doesn't show real-time availability"
- "We need to show up in search results for Asheville hiking" — Jordan
- "Confirmation emails look unprofessional" — Keisha
- "What happens when a guide cancels last minute and we don't have a backup?" — Rachel
- "Customers want to see the guide's bio" — multiple people
- "We don't know if customers are price-sensitive or just not finding us" — Jordan
- "The itinerary PDF takes Keisha 15 minutes each. Times 15 bookings = 3+ hours a week"
- "Payments via Venmo don't feel like a real transaction for corporate group buyers"
- "Trip difficulty ratings aren't standardized — 'moderate' means different things" — Rachel
- "We need to track which bookings came from Instagram vs search vs referral" — Jordan
- "Guide communication needs to be two-way, not just us texting them" — Sam
- "Can customers add a guest after booking?" — Keisha
- "What if two people book the last two spots simultaneously?" (concurrency question from David, flagged during process walkthrough)
- "Need automated reminder emails before trip" — Alex persona reference
- "Roster needs medical flags visible to guide, not just buried in booking form" — Sam
- "We should ask customers their fitness level at booking" — Rachel
- "Payment needs to work on mobile" — multiple
- "What about group discounts?" — Marcus (marked with a star)
- "Can we allow tips to guides through the platform?" — Sam
- "Need to handle partial refunds if customer cancels 7+ days out vs. last minute"
- "Liability waiver needs to be signed before trip" — Patricia (flagged as must-have)
- "The SEO problem is bigger than the booking problem" — Jordan (disputed by Marcus in the room)
- "Trip listings need photos that actually look good" — Jordan
- "Guide assignment should auto-notify when confirmed, not wait for Keisha to text"
- "What's the cancellation policy? It's not written anywhere official" — Patricia
- "We need NPS survey after every trip" — Marcus
- "Customers forget to pack critical gear. We need a checklist in the confirmation."
- "Inventory for rental gear? Do we track that?" — Priya (QA) — *nobody answered this during the workshop*
- "The operations dashboard needs to show all trips, not just this week" — Rachel
- "Different guides have different lead time needs. Can we set preferences per guide?" — Sam
- "Should guides see each other's assignments? Privacy concern?" — Rachel
- "What's the target availability SLA? 99%? 99.9%? Does this run nights and weekends?" — David

---

## Part 2 — Process Walkthrough Summary

*From process walkthrough with Keisha Daniels, Week 3.*

The following is the current booking process mapped during the walkthrough. This is what exists today. It is the baseline for the future-state design.

**Customer Inquiry to Booking Confirmation (current):**

| Step | Who does it | How | Time required | Known failure points |
|------|------------|-----|---------------|---------------------|
| Customer inquires about a trip | Customer | Email or phone call | — | Phone calls go to voicemail ~40% of the time; voicemail response time averages 1–2 business days |
| Check guide/trail availability | Keisha | Reviews Google Sheet | 5–10 min | Sheet is not always up to date; Rachel updates it weekly, not in real time |
| Reply to customer with availability | Keisha | Email | 15–30 min | Emails are manually composed; no template |
| Customer confirms booking | Customer | Replies to email | — | Average 1–3 day gap; some customers don't reply and book elsewhere |
| Confirm guide | Keisha → Guide | Text message | Same day or next day | Guide sometimes unavailable; finding a replacement takes 30–120 min |
| Collect payment | Keisha → Customer | Venmo, Zelle, or check request via email | 1–5 days for check; Venmo/Zelle faster | Checks get lost; Venmo rejected for one corporate group buyer in the past |
| Create and send itinerary PDF | Keisha | Manual PDF creation | 15–20 min per booking | Not standardized; Keisha uses a Word template she maintains herself |
| Log booking in Google Sheet | Keisha | Manual entry | 5 min | Occasionally missed when Keisha is busy; found and corrected at end of week |
| Send pre-trip reminder | Keisha | Email | 15 min | Not always done; Keisha does it when she has time |

**Current process total time per booking (Keisha's estimate):** 45–90 minutes across multiple interactions, spread over 3–5 days.

**Volume:** In peak season, Keisha manages approximately 15–20 active bookings simultaneously. At the high end of the time estimate, this is 30+ hours of booking management work per week — most of Keisha's capacity.

---

## Part 3 — Scope Agreement and Constraints

*Agreed at end of Workshop 2.*

**In scope (MVP):**
1. Customer-facing trip browsing, filtering, and self-serve booking
2. Secure online payment (credit/debit card — Venmo and check remain as fallback only)
3. Automated booking confirmation email with itinerary and packing checklist
4. Internal operations dashboard: confirmed bookings, guide assignment status
5. Guide assignment notification with roster and relevant customer information
6. Signed digital liability waiver at checkout
7. Post-trip NPS survey (automated, 3 days after trip)

**Out of scope (post-MVP backlog):**
- Multi-day expedition booking
- Guide pay processing
- Rental gear inventory
- Group discount pricing
- Customer-to-guide direct messaging
- Trip review/ratings system

**Constraints:**
- Build team: 1 FE, 1 BE, 0.5 QA, 0.5 BA/PM
- Timeline: 10 weeks to working MVP
- Budget: conditional approval (business case must be signed before sprint 3)
- Guide contracts: seasonal and variable — availability data cannot be pulled automatically; must be manually maintained by Rachel or a delegate
- Payment: must be PCI-compliant; no customer payment data stored on-premises

---

## Part 4 — Raw Needs (Not Yet Requirements)

*Compiled from workshops and walkthrough. These are needs — unverified, unsorted, some overlapping or contradictory. Your job in the Session 3 exercise is to work with these, not to receive a clean list.*

**Customer needs (from workshops and persona analysis):**

- Customers want to browse and book a trip without calling or emailing
- Customers want to know the guide's name and qualifications before they commit
- Customers want to see trip difficulty in terms they understand (not just "moderate")
- Customers want a confirmation that looks like a real booking confirmation, not a personal email
- Customers want to know what to bring, specifically, not generically
- Customers who book as a group want one person to be able to manage the booking for the group
- Customers want a way to ask a question after booking without calling during business hours
- Customers may not be on desktop — booking must work on mobile

**Operations needs (from Rachel and Keisha):**

- Operations needs to see all active bookings and guide assignment status in one place, not a Google Sheet
- Operations needs guide assignments confirmed with at least 72 hours' notice for standard trips
- Operations needs the booking process to take less of Keisha's time — ideally close to zero for standard bookings
- Operations needs to be notified when a booking is made (not find out by checking the Sheet)
- Operations needs to be able to update trip availability without a developer involved

**Guide needs (from Sam):**

- Guides need to receive assignment confirmation with sufficient lead time — minimum 72 hours for standard assignments
- Guides need a roster that includes relevant customer information — fitness level, medical flags, group composition
- Guides need a reliable notification channel — not just a text to a personal number
- Guides need to know immediately if customer count or composition changes after assignment
- Guides need access to the meeting point, route details, and emergency contact protocols in one place

**Business/finance needs (from Marcus and Patricia):**

- The business needs to track where bookings are coming from (search, Instagram, referral) to evaluate marketing effectiveness
- The business needs conversion data — how many inquiries become bookings
- The business needs automated payment collection — manual Venmo/Zelle is not scalable
- Payments must be PCI-compliant
- Liability waivers must be collected and stored before the trip
- The business needs pilot NPS data to measure customer experience

---

## A note on what "raw needs" means

A raw need describes what someone wants to be true. It is not yet a requirement.

**Raw need:** "Guides need to receive assignment confirmation with sufficient lead time."
- How much is sufficient? 24 hours? 72 hours? A week?
- For which types of trips? All? Complex groups only?
- What counts as "confirmation"? A text? An email? A notification in an app?
- What happens if confirmation can't be sent with that lead time?

A requirement answers those questions. Your Session 3 exercise is to convert at least 3 of these raw needs into written requirements — statements specific enough that a developer could build to them and a tester could verify them.