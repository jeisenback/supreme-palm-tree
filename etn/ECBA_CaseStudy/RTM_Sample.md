Requirements Traceability Matrix — Sample (excerpt)

--- DOCUMENT GUIDE ---
What this is:   Sample RTM for TrailBlaze — excerpt linking business goals to features, user stories, acceptance tests, and owners.
Who it's for:   Facilitator reference until Session 4; participants receive and expand it as a workshop artifact in Session 4.
When to use it: Session 4 onward.
Restricted:     Yes — do not distribute before Session 4.
--- END GUIDE ---

Session reveal: Session 4.
Facilitator reference until Session 4. Used as a workshop artifact in Session 4 — participants expand from this starting point.

| Business Goal | Feature | User Story ID | Acceptance Test | Owner |
|---------------|---------|---------------|-----------------|-------|
| Increase pilot bookings to 100 | Book a Micro‑Expedition | US-03 | Payment success and confirmation email delivered within 5 min; booking visible in ops dashboard | Product Manager / Ops |
| Improve on‑time departure rate | Ops dashboard & guide assignment | US-04, US-05 | Booking appears in ops dashboard <60s; guide assignment flagged if unconfirmed >12h before trip | Operations Lead |
| Deliver good customer experience (NPS ≥8) | Trip detail + guide bio | US-02 | Trip detail page shows itinerary, guide bio, cancellation policy, and price breakdown | Product Manager |
| Reduce booking inquiry drop‑off | Trip search and filter | US-01 | Search returns results within 500ms; filters visible on mobile; no email required to browse | Product Manager |
| Improve guide communication quality and reduce guide attrition | Guide roster with medical flags and advance notification | US-05 | Guide receives roster with medical flag fields and customer contacts ≥72h before trip | Operations Lead |
| Recover search‑driven new customer acquisition | Trip detail page with SEO‑indexed content | US-02 | Trip detail pages crawlable; metadata includes trail name, difficulty, and location | Marketing Lead |
| Ensure payment security and regulatory compliance | PCI‑compliant checkout | NFR-01 | Sandbox test payment completes without PCI violation; card data not stored by TrailBlaze systems | Engineering Lead |
| Support peak‑volume booking performance | Search and booking response times | NFR-02 | Search latency <500ms at 95th percentile; system stable under 200 concurrent booking sessions | Engineering Lead |

Workshop note: Three rows above (US-01, US-02, NFR-01/02) are intentionally unlabelled in the participant copy — add them as Exercise B expansion targets.
Notes: Use this excerpt as a workshop artifact. Expand to include test case IDs and links to design documents during Exercise B.
