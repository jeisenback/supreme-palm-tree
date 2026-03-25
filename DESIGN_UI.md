# Facilitator UI Design System

## Purpose
This document defines the visual and interaction system for the facilitator presentation experience and the content development workflow in the Board Agents Platform.

## Product Context
The facilitator app serves two high-stakes modes:
1. Live facilitation during workshops where speed, clarity, and confidence matter.
2. Content development where facilitators author, review, and publish session materials.

The UI must prioritize low cognitive load, predictable actions, and clear state.

## Primary Users
- Facilitator: runs live sessions, controls slides, tracks attendance, captures notes.
- Content author: edits session curriculum, creates and uploads decks, generates AI drafts.
- Participant: joins session and follows slides with minimal friction.

## Design Principles
1. State first: always show session state (Not Started, Live, Ended) at the top.
2. One task per surface: avoid mixing presenter controls with authoring controls.
3. Progressive disclosure: hide advanced controls until needed.
4. Human-readable over technical: avoid requiring JSON unless explicitly in advanced mode.
5. Safe by default: destructive actions require confirmation and backup options.

## Visual Direction
Style: Workshop control desk.
Tone: calm, practical, trustworthy.

### Typography
- Headings: Source Serif 4 (or Georgia fallback)
- UI/body: Source Sans 3 (or Segoe UI fallback)
- Code/structured snippets: JetBrains Mono (or Consolas fallback)

### Color Tokens
- --bg-page: #F3F4EF
- --bg-surface: #FFFFFF
- --bg-muted: #ECEDE6
- --text-primary: #1F2A1F
- --text-secondary: #4D5A4D
- --accent-primary: #1E6B52
- --accent-secondary: #C16A2A
- --status-success: #237A4B
- --status-warning: #A66400
- --status-danger: #A12A2A
- --border-subtle: #D4D8CC

### Spatial System
- 4px baseline spacing scale
- Card padding: 16px desktop, 12px mobile
- Section spacing: 24px between major blocks
- Touch target minimum: 40px

## Information Architecture
Use a stable three-zone layout in facilitator mode:
1. Top bar: session state, event title, current variant, quick actions.
2. Main canvas: active step content only.
3. Right rail: facilitator tools (timer, notes, attendee pulse, quick links).

Do not render all major modules at once.

## Core Components
- Session Status Banner: sticky, color-coded by state.
- Step Navigator: segmented control for Overview, Discussion, Notes, Actions, Complete, Case Study, Content.
- Slide Canvas: focused reading width, persistent progress indicator.
- Facilitator Rail: timer, notes, presenter shortcuts.
- Content Workspace: Draft, Review, Publish stages.
- Safety Dialog: used for reset, overwrite, replace, and finalize flows.

## Interaction Patterns
- Navigation controls must be consistent labels everywhere: Previous, Next.
- Keyboard shortcuts should support uppercase and lowercase keys.
- Auto-refresh should be unobtrusive and not reset visible UI state.
- Save actions should provide success message plus location summary.
- Any write action to file should support preview before commit.

## Content Development UX
Replace raw JSON-first authoring with a dual mode:
1. Guided mode (default): form fields for question stem, options, correct answer.
2. Advanced mode: raw JSON editor with schema validation and lint hints.

AI draft workflow should include:
1. Generate
2. Preview as slides
3. Validation check
4. Save as draft
5. Publish to active deck

Upload workflow should include:
- Diff summary (new file vs existing deck)
- Backup checkbox (default on)
- Confirm replace dialog

## Motion and Feedback
- Use subtle fade-in for step changes (150ms to 220ms).
- Use progress transitions on slide move.
- Avoid animated layout shifts.
- Timer urgency transitions: neutral to warning at T-60s and danger at T-10s.

## Accessibility Baseline
- WCAG AA contrast targets for text and controls.
- Keyboard-operable controls for all critical actions.
- Clear focus indicators on interactive elements.
- Avoid color-only status communication.

## Responsive Behavior
- Desktop: main canvas + right rail.
- Tablet: collapsible rail.
- Mobile: stacked single-column flow with persistent session status.

Participant join flow must be visible in main content area on small screens, not sidebar-only.

## Implementation Strategy
Phase 1 (quick wins)
- Normalize navigation labels and control placement.
- Move session status to persistent top banner.
- Split facilitator controls from content authoring into distinct pages/tabs.
- Add confirmations for destructive actions.

Phase 2 (workflow quality)
- Add guided question editor with advanced JSON toggle.
- Add AI draft preview and parse validation gate.
- Add draft-review-publish workflow.

Phase 3 (polish)
- Apply design tokens via centralized style helper.
- Add subtle transitions and improve accessibility cues.
- Add mobile-specific participant join surface.

## Success Metrics
- Reduced facilitator misclicks during live sessions.
- Faster content authoring completion time.
- Lower rate of malformed slide deck saves.
- Higher confidence in post-session export and reset flows.
