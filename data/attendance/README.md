# Attendance Data

**PII NOTICE — RESTRICTED**
Files in this directory contain member names and email addresses.
Do not commit real attendance CSVs to this repository.
Add `data/attendance/sample/*.csv` patterns to `.gitignore` if you add real data.

---

## CSV Format

One CSV per session. Filename convention:

```
data/attendance/YYYYMMDD_session<N>_<type>.csv
```

Examples:
- `20260415_session1_ecba.csv`
- `20260501_ca_career_mapping.csv`

### Columns

| Column | Type | Description |
|--------|------|-------------|
| `date` | YYYY-MM-DD | Session date |
| `session_id` | int or blank | 1–5 for ECBA; CA subtype index for career_accelerator |
| `session_type` | string | `ecba_session`, `career_accelerator`, or `panel_event` |
| `member_email` | string | Primary key for member identity |
| `member_name` | string | Display name (First Last) |
| `attended` | TRUE/FALSE | Whether the member attended |
| `homework_submitted` | TRUE/FALSE | Whether homework was submitted before this session |

### Rules

- One row per member per session
- `attended` = FALSE rows are allowed for no-shows (enables roster tracking)
- `homework_submitted` refers to homework *for this session* (assigned at the prior session)
- Email is the stable identifier — names may change

---

## Ingest

Run from the project root:

```bash
python apps/learner_tracking.py ingest data/attendance/
```

This scans all CSV files under `data/attendance/`, ingests them into
`data/learner_records.db` (SQLite), and prints a summary.

---

## Schema location

Template CSV: `data/attendance/attendance_template.csv`
Sample CSV: `data/attendance/sample/20260401_session1_ecba.csv`
