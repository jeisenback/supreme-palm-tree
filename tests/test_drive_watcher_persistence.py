from pathlib import Path
import json

from agents.watcher import _load_seen, _save_seen


def test_save_and_load_seen(tmp_path: Path):
    fp = tmp_path / "seen.json"
    s = {"a1", "b2", "c3"}
    _save_seen(fp, s)
    assert fp.exists()
    got = _load_seen(fp)
    assert s == got
