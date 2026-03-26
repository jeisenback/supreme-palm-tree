# ECBA Board Showcase — Deployment Guide

A clean, no-login Streamlit app that presents the ECBA certification study
program to IIBA East TN board members and prospective participants.

## Quick Start

From the repo root:

```bash
bash scripts/start_board_showcase.sh
```

Opens at **http://localhost:8502**

To use a different port:

```bash
bash scripts/start_board_showcase.sh 8503
```

## Manual Start

```bash
streamlit run apps/board_showcase.py --server.port 8502
```

## What the App Shows

| Section | Content |
|---|---|
| Hero | Program name, tagline, key stats (5 sessions, Apr–Aug, Virtual) |
| The Program | 5-session curriculum timeline — click each session for agenda + prompts |
| A Glimpse Inside | 3 slide cards from the curriculum (requires variant folder) |
| Try It Yourself | Interactive practice MCQ with instant feedback |
| The TrailBlaze Case Study | Plain-English description of the case study through-line |
| Explore All Materials | Full document browser — click any file to view inline |

## Requirements

### Python dependencies

Same as the facilitator UI — no additional packages needed:

```bash
pip install -r requirements.txt
```

### Variant folder (optional)

The app works without any local data — Sections 1, 2, 4, and 5 are
hardcoded from the curriculum. To enable slide cards and document browsing,
place a variant folder under `etn/`:

```
etn/
  ECBA_CaseStudy_<variant>/
    TrailBlaze_MasterContext.md   ← required for variant to be detected
    <slides>.md                   ← detected by "slide" in filename
    *.md, *.txt, *.csv            ← shown in document browser
```

## Running Both Apps Simultaneously

The facilitator UI defaults to port 8501. Run the board showcase on 8502:

```bash
# Terminal 1 — facilitator UI
bash apps/start_facilitator.sh          # or: streamlit run apps/facilitator_ui.py

# Terminal 2 — board showcase
bash scripts/start_board_showcase.sh    # port 8502
```

## Sharing with Board Members

The board showcase requires **no login**. Share the URL directly:

- Local demo: `http://localhost:8502`
- If hosting on a server: replace `localhost` with the server IP or hostname

No password, no setup required on the viewer's side.

## Architecture

```
apps/
  board_showcase.py       ← this app
  facilitator_ui.py       ← facilitator tool (separate audience)
  shared.py               ← shared utilities (SESSIONS data, file I/O, slide parser)

.streamlit/
  config.toml             ← IIBA East TN brand theme (orange #DB5D00, navy #002E38)

scripts/
  start_board_showcase.sh ← startup script
```

Both apps import from `apps/shared.py`. Changes to session content or
utility functions only need to be made in one place.
