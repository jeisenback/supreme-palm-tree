## Session management for interactive agent use

Purpose: define how the agent should manage conversational state, session ids,
and when to persist or clear context across user interactions.

Session Rules
- Each interactive session should have a stable `session_id` that can be
  referenced by the user or system for continuity.
- Persist only non-sensitive session metadata (timestamps, last_action, tags).
  Do not store PII in session storage.

Timeouts and Cleanup
- Sessions should expire after a configurable idle timeout (e.g., 30 minutes).
- When a session expires, emit a short summary of the last state and clear
  ephemeral buffers.

Human Handoff
- When a user requests human review or approval, mark the session state as
  `awaiting_human` and provide an exportable artifact (markdown summary and
  file links) that reviewers can use to approve changes.
