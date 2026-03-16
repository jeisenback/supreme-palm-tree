import json
from agents.agents_cli import main


def test_cli_accelerator(capsys, tmp_path):
    apps = {"a1": {"focus": "tech"}}
    p = tmp_path / "apps.json"
    p.write_text(json.dumps(apps), encoding="utf-8")

    rc = main(["role", "accelerator", "--json-file", str(p)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Select top applicants" in captured.out or "mentor" in captured.out.lower()
