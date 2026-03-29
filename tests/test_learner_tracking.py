"""
tests/test_learner_tracking.py

Unit tests for apps/learner_tracking.py — no Streamlit imports.
"""

import csv
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))
from learner_tracking import (
    get_board_metrics,
    get_learner_summary,
    ingest_csv,
    ingest_directory,
    init_db,
    readiness_score,
)

_SAMPLE_DIR = Path(__file__).parent.parent / "data" / "attendance" / "sample"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["date", "session_id", "session_type", "member_email",
                  "member_name", "attended", "homework_submitted"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _row(email="a@x.com", name="Alice", session_id=1, session_type="ecba_session",
         date="2026-04-01", attended="TRUE", homework="FALSE"):
    return {
        "date": date, "session_id": session_id, "session_type": session_type,
        "member_email": email, "member_name": name,
        "attended": attended, "homework_submitted": homework,
    }


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

class TestInitDb:
    def test_creates_members_table(self, tmp_path):
        db = tmp_path / "test.db"
        conn = init_db(db)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert "members" in tables
        assert "attendance" in tables
        conn.close()

    def test_idempotent(self, tmp_path):
        db = tmp_path / "test.db"
        init_db(db).close()
        # Second call should not raise
        conn = init_db(db)
        count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        assert count == 0
        conn.close()

    def test_creates_parent_dir(self, tmp_path):
        db = tmp_path / "sub" / "dir" / "learner.db"
        conn = init_db(db)
        conn.close()
        assert db.exists()


# ---------------------------------------------------------------------------
# ingest_csv
# ---------------------------------------------------------------------------

class TestIngestCsv:
    def test_happy_path_single_row(self, tmp_path):
        csv_path = _write_csv(tmp_path / "s1.csv", [_row()])
        db = tmp_path / "l.db"
        result = ingest_csv(csv_path, db)
        assert result["rows_processed"] == 1
        assert result["members_new"] == 1
        assert not result["errors"]

    def test_member_created_in_db(self, tmp_path):
        csv_path = _write_csv(tmp_path / "s1.csv", [_row(email="b@x.com", name="Bob")])
        db = tmp_path / "l.db"
        ingest_csv(csv_path, db)
        conn = sqlite3.connect(str(db))
        member = conn.execute("SELECT * FROM members WHERE email=?", ("b@x.com",)).fetchone()
        conn.close()
        assert member is not None

    def test_attendance_row_created(self, tmp_path):
        csv_path = _write_csv(tmp_path / "s1.csv", [_row(attended="TRUE", homework="FALSE")])
        db = tmp_path / "l.db"
        ingest_csv(csv_path, db)
        conn = sqlite3.connect(str(db))
        row = conn.execute("SELECT attended, homework_submitted FROM attendance").fetchone()
        conn.close()
        assert row[0] == 1
        assert row[1] == 0

    def test_attendance_false_parsed(self, tmp_path):
        csv_path = _write_csv(tmp_path / "s1.csv", [_row(attended="FALSE", homework="TRUE")])
        db = tmp_path / "l.db"
        ingest_csv(csv_path, db)
        conn = sqlite3.connect(str(db))
        row = conn.execute("SELECT attended, homework_submitted FROM attendance").fetchone()
        conn.close()
        assert row[0] == 0
        assert row[1] == 1

    def test_missing_columns_returns_error(self, tmp_path):
        bad = tmp_path / "bad.csv"
        bad.write_text("email,name\na@x.com,Alice\n", encoding="utf-8")
        db = tmp_path / "l.db"
        result = ingest_csv(bad, db)
        assert result["errors"]
        assert result["rows_processed"] == 0

    def test_duplicate_row_does_not_duplicate(self, tmp_path):
        row = _row()
        csv_path = _write_csv(tmp_path / "s1.csv", [row, row])
        db = tmp_path / "l.db"
        ingest_csv(csv_path, db)
        conn = sqlite3.connect(str(db))
        count = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        conn.close()
        assert count == 1

    def test_upsert_updates_existing_member_name(self, tmp_path):
        csv1 = _write_csv(tmp_path / "s1.csv", [_row(email="c@x.com", name="Carla")])
        csv2 = _write_csv(tmp_path / "s2.csv", [
            _row(email="c@x.com", name="Carla M.", session_id=2, date="2026-04-15")
        ])
        db = tmp_path / "l.db"
        ingest_csv(csv1, db)
        ingest_csv(csv2, db)
        conn = sqlite3.connect(str(db))
        name = conn.execute("SELECT name FROM members WHERE email=?", ("c@x.com",)).fetchone()[0]
        conn.close()
        assert name == "Carla M."

    def test_multiple_members(self, tmp_path):
        rows = [_row("a@x.com", "Alice"), _row("b@x.com", "Bob"), _row("c@x.com", "Carla")]
        csv_path = _write_csv(tmp_path / "s.csv", rows)
        db = tmp_path / "l.db"
        result = ingest_csv(csv_path, db)
        assert result["members_new"] == 3
        assert result["rows_processed"] == 3


# ---------------------------------------------------------------------------
# ingest_directory
# ---------------------------------------------------------------------------

class TestIngestDirectory:
    def test_skips_template_csv(self, tmp_path):
        (tmp_path / "attendance_template.csv").write_text(
            "date,session_id,session_type,member_email,member_name,attended,homework_submitted\n",
            encoding="utf-8",
        )
        db = tmp_path / "l.db"
        results = ingest_directory(tmp_path, db)
        assert results == []

    def test_ingests_multiple_csvs(self, tmp_path):
        _write_csv(tmp_path / "20260401_s1.csv", [_row()])
        _write_csv(tmp_path / "20260415_s2.csv", [_row(session_id=2, date="2026-04-15")])
        db = tmp_path / "l.db"
        results = ingest_directory(tmp_path, db)
        assert len(results) == 2

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        results = ingest_directory(tmp_path / "nodir", tmp_path / "l.db")
        assert results == []

    def test_uses_sample_csvs(self):
        """Smoke test against the real sample CSVs."""
        if not _SAMPLE_DIR.exists():
            pytest.skip("Sample dir not present")
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db = Path(f.name)
        try:
            results = ingest_directory(_SAMPLE_DIR, db)
            assert len(results) >= 1
            assert all(not r["errors"] for r in results)
        finally:
            os.unlink(db)


# ---------------------------------------------------------------------------
# readiness_score
# ---------------------------------------------------------------------------

class TestReadinessScore:
    def test_zero_zero(self):
        assert readiness_score(0, 0) == 0

    def test_max_score(self):
        assert readiness_score(5, 5) == 100

    def test_partial_attendance_only(self):
        # 2 sessions attended, no hw: 2*15/100 * 100 = 30
        assert readiness_score(2, 0) == 30

    def test_partial_with_homework(self):
        # 2 sessions + 1 hw: (30+5)/100*100 = 35
        assert readiness_score(2, 1) == 35

    def test_capped_at_100(self):
        assert readiness_score(10, 10) == 100

    def test_returns_int(self):
        assert isinstance(readiness_score(3, 2), int)


# ---------------------------------------------------------------------------
# get_learner_summary
# ---------------------------------------------------------------------------

class TestGetLearnerSummary:
    def test_empty_db_returns_empty_list(self, tmp_path):
        db = tmp_path / "l.db"
        init_db(db).close()
        assert get_learner_summary(db) == []

    def test_single_member_shows_in_summary(self, tmp_path):
        csv_path = _write_csv(tmp_path / "s.csv", [_row(attended="TRUE", homework="TRUE")])
        db = tmp_path / "l.db"
        ingest_csv(csv_path, db)
        summary = get_learner_summary(db)
        assert len(summary) == 1
        assert summary[0]["ecba_sessions_attended"] == 1
        assert summary[0]["ecba_homework"] == 1
        assert summary[0]["readiness_score"] == 20  # 1*15 + 1*5 = 20

    def test_ordering_by_readiness_desc(self, tmp_path):
        rows = [
            _row("low@x.com", "Low", attended="FALSE", homework="FALSE"),
            _row("high@x.com", "High", attended="TRUE", homework="TRUE"),
            _row("mid@x.com", "Mid", attended="TRUE", homework="FALSE"),
        ]
        csv_path = _write_csv(tmp_path / "s.csv", rows)
        db = tmp_path / "l.db"
        ingest_csv(csv_path, db)
        summary = get_learner_summary(db)
        scores = [r["readiness_score"] for r in summary]
        assert scores == sorted(scores, reverse=True)

    def test_summary_has_required_keys(self, tmp_path):
        csv_path = _write_csv(tmp_path / "s.csv", [_row()])
        db = tmp_path / "l.db"
        ingest_csv(csv_path, db)
        record = get_learner_summary(db)[0]
        for key in ("email", "name", "sessions_attended", "homework_submitted",
                    "ecba_sessions_attended", "ecba_homework", "readiness_score"):
            assert key in record, f"Missing key: {key}"

    def test_non_attended_row_not_counted(self, tmp_path):
        csv_path = _write_csv(tmp_path / "s.csv", [_row(attended="FALSE", homework="FALSE")])
        db = tmp_path / "l.db"
        ingest_csv(csv_path, db)
        summary = get_learner_summary(db)
        assert summary[0]["ecba_sessions_attended"] == 0
        assert summary[0]["readiness_score"] == 0


# ---------------------------------------------------------------------------
# get_board_metrics
# ---------------------------------------------------------------------------

class TestGetBoardMetrics:
    def test_empty_db_returns_zeros(self, tmp_path):
        db = tmp_path / "l.db"
        init_db(db).close()
        metrics = get_board_metrics(db)
        assert metrics["total_members"] == 0
        assert metrics["avg_attendance_rate"] == 0.0
        assert metrics["homework_completion_rate"] == 0.0
        assert metrics["top_readiness_score"] == 0
        assert metrics["avg_readiness_score"] == 0.0

    def test_metrics_after_ingest(self, tmp_path):
        rows = [
            _row("a@x.com", "Alice", attended="TRUE", homework="TRUE"),
            _row("b@x.com", "Bob", attended="TRUE", homework="FALSE"),
            _row("c@x.com", "Carol", attended="FALSE", homework="FALSE"),
        ]
        csv_path = _write_csv(tmp_path / "s.csv", rows)
        db = tmp_path / "l.db"
        ingest_csv(csv_path, db)
        metrics = get_board_metrics(db)
        assert metrics["total_members"] == 3
        assert metrics["total_sessions_logged"] == 3
        # 2/3 attended
        assert abs(metrics["avg_attendance_rate"] - 2 / 3) < 0.01
        # 1/2 homework (of those who attended)
        assert abs(metrics["homework_completion_rate"] - 0.5) < 0.01

    def test_metrics_has_required_keys(self, tmp_path):
        db = tmp_path / "l.db"
        init_db(db).close()
        metrics = get_board_metrics(db)
        for key in ("total_members", "total_sessions_logged", "avg_attendance_rate",
                    "homework_completion_rate", "top_readiness_score", "avg_readiness_score"):
            assert key in metrics

    def test_top_readiness_is_max(self, tmp_path):
        rows = [
            _row("a@x.com", "Alice", attended="TRUE", homework="TRUE"),
            _row("b@x.com", "Bob", attended="FALSE", homework="FALSE"),
        ]
        csv_path = _write_csv(tmp_path / "s.csv", rows)
        db = tmp_path / "l.db"
        ingest_csv(csv_path, db)
        metrics = get_board_metrics(db)
        # Alice: 1*15 + 1*5 = 20; Bob: 0
        assert metrics["top_readiness_score"] == 20
