from pathlib import Path
import shutil

from agents.weekly_update import gather_notes, compose_weekly_update, write_weekly_update


def test_gather_and_compose(tmp_path: Path):
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    (notes_dir / "note1.md").write_text("# Note 1\n\nContent A")
    (notes_dir / "note2.txt").write_text("Meeting notes\n- item")

    files = gather_notes(str(notes_dir))
    assert len(files) == 2

    md = compose_weekly_update(title="Test Update", notes_dir=str(notes_dir), use_llm=False)
    assert "# Test Update" in md
    assert "## note1.md" in md

    out = tmp_path / "out" / "weekly.md"
    p = write_weekly_update(str(out), title="Test Update", notes_dir=str(notes_dir), use_llm=False)
    assert p.exists()
    txt = p.read_text()
    assert "Meeting notes" in txt
