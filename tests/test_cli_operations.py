import json
from agents.agents_cli import main


def test_cli_operations(capsys, tmp_path):
    ctx = {"facilities": False, "compliance": False}
    p = tmp_path / "ops.json"
    p.write_text(json.dumps(ctx), encoding="utf-8")

    rc = main(["role", "operations", "--json-file", str(p)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Review facilities" in captured.out or "Validate finance controls" in captured.out
