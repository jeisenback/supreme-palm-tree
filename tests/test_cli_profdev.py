import json
from agents.agents_cli import main


def test_cli_profdev_from_json(capsys, tmp_path):
    mapping = {"python": 5, "fundraising": 2, "governance": 3}
    p = tmp_path / "skills.json"
    p.write_text(json.dumps(mapping), encoding="utf-8")

    rc = main(["role", "professional_development", "--json-file", str(p)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "recommendation" in captured.out.lower() or "-" in captured.out
