"""
apps/learner_tracking.py

Attendance ingest and learner metrics for the IIBA ETN curriculum platform.

No Streamlit imports — safe to use in tests and as a CLI script.

Usage (CLI):
    python apps/learner_tracking.py ingest [attendance_dir] [db_path]
    python apps/learner_tracking.py status [db_path]
"""

import csv
import sqlite3
from pathlib import Path
from datetime import date as _date

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_DB = Path(__file__).parent.parent / "data" / "learner_records.db"
_DEFAULT_ATTENDANCE_DIR = Path(__file__).parent.parent / "data" / "attendance"

# Points per ECBA session (max 5 sessions = 100 pts total)
_ATTENDANCE_POINTS = 15
_HOMEWORK_POINTS = 5
_ECBA_SESSION_COUNT = 5
_MAX_SCORE = _ECBA_SESSION_COUNT * (_ATTENDANCE_POINTS + _HOMEWORK_POINTS)  # 100


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
    email       TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    first_seen  TEXT
);

CREATE TABLE IF NOT EXISTS attendance (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    member_email        TEXT NOT NULL REFERENCES members(email),
    session_date        TEXT NOT NULL,
    session_id          INTEGER,
    session_type        TEXT NOT NULL DEFAULT 'ecba_session',
    attended            INTEGER NOT NULL DEFAULT 0,
    homework_submitted  INTEGER NOT NULL DEFAULT 0,
    UNIQUE(member_email, session_date, session_id, session_type)
);
"""


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def init_db(db_path: Path = _DEFAULT_DB) -> sqlite3.Connection:
    """Create the database schema if it doesn't exist and return a connection.

    The database file (and parent dir) are created if absent.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def _bool(value: str) -> int:
    """Parse a CSV boolean column (TRUE/FALSE/1/0/yes/no) → 0 or 1."""
    return int(str(value).strip().upper() in ("TRUE", "1", "YES", "Y"))


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

def ingest_csv(csv_path: Path, db_path: Path = _DEFAULT_DB) -> dict:
    """Ingest one attendance CSV file into the database.

    Returns a summary dict:
        {rows_processed, rows_inserted, rows_updated, members_new, errors}
    """
    csv_path = Path(csv_path)
    summary = {"rows_processed": 0, "rows_inserted": 0, "rows_updated": 0,
               "members_new": 0, "errors": []}

    conn = init_db(db_path)
    try:
        with open(csv_path, encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            required = {"date", "session_type", "member_email", "member_name",
                        "attended", "homework_submitted"}
            if not required.issubset(set(reader.fieldnames or [])):
                missing = required - set(reader.fieldnames or [])
                summary["errors"].append(f"Missing columns: {missing}")
                return summary

            for row in reader:
                summary["rows_processed"] += 1
                email = row["member_email"].strip().lower()
                name = row["member_name"].strip()
                session_date = row["date"].strip()
                session_type = row["session_type"].strip()
                session_id_raw = row.get("session_id", "").strip()
                session_id = int(session_id_raw) if session_id_raw.isdigit() else None
                attended = _bool(row["attended"])
                homework = _bool(row["homework_submitted"])

                # Upsert member
                existing = conn.execute(
                    "SELECT 1 FROM members WHERE email = ?", (email,)
                ).fetchone()
                if not existing:
                    conn.execute(
                        "INSERT INTO members(email, name, first_seen) VALUES(?,?,?)",
                        (email, name, session_date),
                    )
                    summary["members_new"] += 1
                else:
                    # Update name if it changed
                    conn.execute(
                        "UPDATE members SET name = ? WHERE email = ?", (name, email)
                    )

                # Upsert attendance
                cur = conn.execute(
                    """INSERT INTO attendance
                           (member_email, session_date, session_id, session_type,
                            attended, homework_submitted)
                       VALUES (?,?,?,?,?,?)
                       ON CONFLICT(member_email, session_date, session_id, session_type)
                       DO UPDATE SET attended=excluded.attended,
                                     homework_submitted=excluded.homework_submitted""",
                    (email, session_date, session_id, session_type, attended, homework),
                )
                if cur.rowcount and cur.lastrowid:
                    # SQLite UPSERT: rowcount=1 on both insert+update, use lastrowid
                    summary["rows_inserted"] += 1
                else:
                    summary["rows_updated"] += 1

        conn.commit()
    except Exception as exc:
        summary["errors"].append(str(exc))
    finally:
        conn.close()

    return summary


def ingest_directory(dir_path: Path = _DEFAULT_ATTENDANCE_DIR,
                     db_path: Path = _DEFAULT_DB) -> list[dict]:
    """Ingest all CSV files in dir_path (non-recursive) into db_path.

    Returns a list of per-file summary dicts (same shape as ingest_csv).
    Skips files named 'attendance_template.csv' and non-.csv files.
    """
    dir_path = Path(dir_path)
    results = []
    if not dir_path.exists():
        return results

    for csv_file in sorted(dir_path.glob("*.csv")):
        if csv_file.name == "attendance_template.csv":
            continue
        result = ingest_csv(csv_file, db_path)
        result["file"] = csv_file.name
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_learner_summary(db_path: Path = _DEFAULT_DB) -> list[dict]:
    """Return one dict per member, ordered by readiness score descending.

    Keys: email, name, sessions_attended, homework_submitted,
          readiness_score (0-100), ecba_sessions_attended, ecba_homework
    """
    conn = init_db(db_path)
    try:
        rows = conn.execute("""
            SELECT
                m.email,
                m.name,
                SUM(CASE WHEN a.attended = 1 THEN 1 ELSE 0 END)             AS sessions_attended,
                SUM(CASE WHEN a.homework_submitted = 1 THEN 1 ELSE 0 END)   AS homework_submitted,
                SUM(CASE WHEN a.session_type = 'ecba_session'
                          AND a.attended = 1 THEN 1 ELSE 0 END)              AS ecba_sessions_attended,
                SUM(CASE WHEN a.session_type = 'ecba_session'
                          AND a.homework_submitted = 1 THEN 1 ELSE 0 END)   AS ecba_homework
            FROM members m
            LEFT JOIN attendance a ON a.member_email = m.email
            GROUP BY m.email, m.name
        """).fetchall()
    finally:
        conn.close()

    result = []
    for row in rows:
        score = readiness_score(row["ecba_sessions_attended"] or 0,
                                row["ecba_homework"] or 0)
        result.append({
            "email": row["email"],
            "name": row["name"],
            "sessions_attended": row["sessions_attended"] or 0,
            "homework_submitted": row["homework_submitted"] or 0,
            "ecba_sessions_attended": row["ecba_sessions_attended"] or 0,
            "ecba_homework": row["ecba_homework"] or 0,
            "readiness_score": score,
        })

    return sorted(result, key=lambda r: r["readiness_score"], reverse=True)


def readiness_score(ecba_sessions_attended: int, ecba_homework_submitted: int) -> int:
    """Estimate ECBA exam readiness as a 0–100 score.

    Formula: (attended * 15 + homework * 5) / 100 * 100, capped at 100.
    Each of the 5 sessions is worth 15 pts attendance + 5 pts homework = 100 max.
    """
    raw = (ecba_sessions_attended * _ATTENDANCE_POINTS
           + ecba_homework_submitted * _HOMEWORK_POINTS)
    return min(100, int(raw / _MAX_SCORE * 100))


def get_board_metrics(db_path: Path = _DEFAULT_DB) -> dict:
    """Return chapter-level metrics for board reporting.

    Keys:
        total_members         — unique member count
        total_sessions_logged — distinct (member, session_date, session_id) rows
        avg_attendance_rate   — fraction of attended rows / total rows (0.0–1.0)
        homework_completion_rate — fraction of homework_submitted / attended rows
        top_readiness_score   — highest individual score
        avg_readiness_score   — mean across all members
    """
    conn = init_db(db_path)
    try:
        total_members = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        total_rows = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        attended_rows = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE attended = 1"
        ).fetchone()[0]
        homework_rows = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE homework_submitted = 1 AND attended = 1"
        ).fetchone()[0]
    finally:
        conn.close()

    summary = get_learner_summary(db_path)

    return {
        "total_members": total_members,
        "total_sessions_logged": total_rows,
        "avg_attendance_rate": round(attended_rows / total_rows, 3) if total_rows else 0.0,
        "homework_completion_rate": round(homework_rows / attended_rows, 3) if attended_rows else 0.0,
        "top_readiness_score": max((r["readiness_score"] for r in summary), default=0),
        "avg_readiness_score": round(
            sum(r["readiness_score"] for r in summary) / len(summary), 1
        ) if summary else 0.0,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "ingest":
        attendance_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else _DEFAULT_ATTENDANCE_DIR
        db = Path(sys.argv[3]) if len(sys.argv) > 3 else _DEFAULT_DB
        results = ingest_directory(attendance_dir, db)
        if not results:
            print(f"No CSV files found in {attendance_dir}")
        for r in results:
            status_str = "OK" if not r["errors"] else f"ERRORS: {r['errors']}"
            print(f"  {r['file']}: {r['rows_processed']} rows, "
                  f"{r['members_new']} new members — {status_str}")
        print(f"\nDatabase: {db}")

    elif cmd == "status":
        db = Path(sys.argv[2]) if len(sys.argv) > 2 else _DEFAULT_DB
        metrics = get_board_metrics(db)
        print(f"Members:           {metrics['total_members']}")
        print(f"Sessions logged:   {metrics['total_sessions_logged']}")
        print(f"Attendance rate:   {metrics['avg_attendance_rate']:.0%}")
        print(f"Homework rate:     {metrics['homework_completion_rate']:.0%}")
        print(f"Avg readiness:     {metrics['avg_readiness_score']}/100")
        print(f"Top readiness:     {metrics['top_readiness_score']}/100")

    else:
        print(f"Unknown command: {cmd!r}. Use 'ingest' or 'status'.")
        sys.exit(1)
