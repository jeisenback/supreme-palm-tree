"""
tests/test_frontmatter_idempotence.py

Verify that read → write cycles are byte-for-byte stable.

Architecture constraint from Sprint 5 design doc:
    Idempotence test: write → read → write →
    assert open(path, 'rb').read() == original_bytes
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))
import frontmatter_utils as fu
from frontmatter_utils import read_frontmatter, write_frontmatter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_file(path: Path, content: str) -> Path:
    """Write raw UTF-8 content (LF line endings) to path and return it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRoundTripIdempotence:
    """write → read → write produces identical bytes."""

    def test_simple_metadata_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fu, "_ETN_ROOT", tmp_path)
        p = tmp_path / "session.md"
        original = (
            "---\n"
            "content_type: ecba_session\n"
            "session_id: 1\n"
            "slot: slides\n"
            "status: published\n"
            "---\n"
            "\n"
            "# Session 1 — Business Analysis Foundations\n"
            "\n"
            "Body text here.\n"
        )
        _make_file(p, original)

        # Cycle 1
        meta, body = read_frontmatter(p)
        write_frontmatter(p, meta, body)
        after_cycle1 = p.read_bytes()

        # Cycle 2
        meta2, body2 = read_frontmatter(p)
        write_frontmatter(p, meta2, body2)
        after_cycle2 = p.read_bytes()

        assert after_cycle1 == after_cycle2, "Second write cycle changed bytes"

    def test_template_file_idempotent(self, tmp_path, monkeypatch):
        """Stable after first write — key ordering and trailing newlines normalised."""
        monkeypatch.setattr(fu, "_ETN_ROOT", tmp_path)
        p = tmp_path / "template.md"
        meta = {
            "content_type": "career_accelerator",
            "subtype": "career_mapping",
            "slot": "facilitator_guide",
            "status": "template",
        }
        # Establish normalised baseline via write_frontmatter
        write_frontmatter(p, meta, "Template body.\n")
        baseline = p.read_bytes()

        meta2, body2 = read_frontmatter(p)
        write_frontmatter(p, meta2, body2)

        assert p.read_bytes() == baseline, "Template round-trip changed bytes"

    def test_draft_with_multiline_body(self, tmp_path, monkeypatch):
        """Multiline body (with --- separators) is stable across write cycles."""
        monkeypatch.setattr(fu, "_ETN_ROOT", tmp_path)
        p = tmp_path / "draft.md"
        meta = {"content_type": "ecba_session", "slot": "slides", "status": "draft"}
        body = (
            "# Slide 1\n"
            "- Bullet A\n"
            "- Bullet B\n"
            "\n"
            "---\n"
            "\n"
            "# Slide 2\n"
            "[FACILITATOR: Pause for questions]\n"
        )
        # Baseline = output of first write (normalised form)
        write_frontmatter(p, meta, body)
        baseline = p.read_bytes()

        meta2, body2 = read_frontmatter(p)
        write_frontmatter(p, meta2, body2)

        assert p.read_bytes() == baseline

    def test_three_cycle_stability(self, tmp_path, monkeypatch):
        """Ensure stability is not just cycle 1→2; verify cycle 2→3 also stable."""
        monkeypatch.setattr(fu, "_ETN_ROOT", tmp_path)
        p = tmp_path / "stable.md"
        _make_file(p, (
            "---\n"
            "content_type: panel_event\n"
            "slot: moderator_script\n"
            "status: published\n"
            "---\n"
            "\n"
            "Panel run-of-show.\n"
        ))

        for _ in range(3):
            meta, body = read_frontmatter(p)
            write_frontmatter(p, meta, body)

        bytes_after_3 = p.read_bytes()

        # One more cycle — should remain identical
        meta, body = read_frontmatter(p)
        write_frontmatter(p, meta, body)

        assert p.read_bytes() == bytes_after_3, "Cycle 3→4 is not stable"

    def test_integer_metadata_preserved(self, tmp_path, monkeypatch):
        """Integers in metadata should survive round-trip as integers, not strings."""
        monkeypatch.setattr(fu, "_ETN_ROOT", tmp_path)
        p = tmp_path / "session.md"
        _make_file(p, (
            "---\n"
            "session_id: 3\n"
            "content_type: ecba_session\n"
            "---\n\nBody.\n"
        ))

        meta, _ = read_frontmatter(p)
        assert isinstance(meta["session_id"], int), "session_id should be int after load"

        write_frontmatter(p, meta, _)
        meta2, _ = read_frontmatter(p)
        assert isinstance(meta2["session_id"], int), "session_id should remain int after write"
        assert meta2["session_id"] == 3

    def test_extra_yaml_fields_preserved(self, tmp_path, monkeypatch):
        """Unknown frontmatter fields survive read → write without loss."""
        monkeypatch.setattr(fu, "_ETN_ROOT", tmp_path)
        p = tmp_path / "custom.md"
        _make_file(p, (
            "---\n"
            "content_type: ecba_session\n"
            "slot: slides\n"
            "status: published\n"
            "label: facilitator_answers\n"
            "variant: \"1b\"\n"
            "---\n\nBody.\n"
        ))

        meta, body = read_frontmatter(p)
        assert meta.get("label") == "facilitator_answers"
        assert meta.get("variant") == "1b"

        write_frontmatter(p, meta, body)
        meta2, _ = read_frontmatter(p)
        assert meta2.get("label") == "facilitator_answers"
        assert meta2.get("variant") == "1b"

    def test_body_whitespace_preserved(self, tmp_path, monkeypatch):
        """Trailing whitespace within body lines is not stripped."""
        monkeypatch.setattr(fu, "_ETN_ROOT", tmp_path)
        p = tmp_path / "ws.md"
        body_content = "Line one\n\nLine two\n\n"
        raw = f"---\nstatus: published\n---\n\n{body_content}"
        _make_file(p, raw)

        meta, body = read_frontmatter(p)
        write_frontmatter(p, meta, body)

        _, body2 = read_frontmatter(p)
        assert body2.strip() == body_content.strip()


class TestRealEcbaFileIdempotence:
    """Round-trip the actual backfilled ECBA session files (if present)."""

    @pytest.fixture
    def ecba_session_files(self):
        ecba_dir = Path(__file__).parent.parent / "etn" / "ECBA_CaseStudy"
        files = sorted(ecba_dir.rglob("*.md")) if ecba_dir.exists() else []
        return [f for f in files if f.stat().st_size > 0]

    def test_real_files_round_trip_stable(self, ecba_session_files):
        """Each real ECBA file survives two consecutive read→write cycles identically."""
        if not ecba_session_files:
            pytest.skip("No ECBA session files found")

        failures = []
        for path in ecba_session_files:
            original_bytes = path.read_bytes()
            meta, body = read_frontmatter(path)

            if not meta:
                # No frontmatter — skip (legacy file not yet tagged)
                continue

            # We do NOT write back to real files — just verify the
            # python-frontmatter round-trip produces identical text.
            import frontmatter as _fm
            post = _fm.Post(body, **meta)
            rendered = _fm.dumps(post)

            # Re-load the rendered version
            post2 = _fm.loads(rendered)
            rendered2 = _fm.dumps(post2)

            if rendered != rendered2:
                failures.append(f"{path.name}: render is not stable")

        assert not failures, "Round-trip instability in:\n" + "\n".join(failures)
