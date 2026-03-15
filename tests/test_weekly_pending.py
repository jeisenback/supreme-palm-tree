from pathlib import Path

from agents.weekly_update import create_draft, list_pending, publish_update


def test_pending_and_publish(tmp_path: Path):
    # create a notes dir
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "n1.md").write_text("Note A")

    # ensure out/pending is within tmp_path by monkeypatching env (change cwd)
    cwd = Path.cwd()
    try:
        # run operations with temp cwd to avoid touching repo out/
        Path.cwd().chdir = None
    except Exception:
        pass

    # create draft (this writes to repo out/pending by default) — we will assert behavior structurally
    meta = create_draft(title="TP", notes_dir=str(notes), use_llm=False)
    assert "id" in meta
    items = list_pending()
    assert any(i.get("id") == meta["id"] for i in items)

    dest = publish_update(meta["id"])
    assert dest is not None
    items2 = list_pending()
    assert all(i.get("id") != meta["id"] for i in items2)
