import json
from agents.agents_cli import main


def test_role_fundraising_outputs_plan(capsys):
    rc = main(["role", "fundraising", "--csv", "donor,amount\nAlice,100\nBob,50\n"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Reach out to top donors" in captured.out


def test_role_membership_outputs_insights(capsys):
    rc = main(["role", "membership", "--csv", "member_id,joined_date,status\n1,2022-01-01,active\n2,2021-06-01,lapsed\n"])
    assert rc == 0
    captured = capsys.readouterr()
    # membership_summary_markdown includes 'Total members' header
    assert "Membership Summary" in captured.out or "Total members" in captured.out


def test_role_communications_draft_and_email(capsys, tmp_path):
    ctx = {"title": "Update", "audience": "members", "summary": "Brief update", "call_to_action": "Join us"}
    p = tmp_path / "ctx.json"
    p.write_text(json.dumps(ctx), encoding="utf-8")

    # Draft
    rc = main(["role", "communications", "--json-file", str(p)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Update" in captured.out

    # Email campaign
    rc = main(["role", "communications", "--json-file", str(p), "--subject", "Event", "--audience", "members"])
    assert rc == 0
    captured = capsys.readouterr()
    # Should output JSON with subject/body
    assert "subject" in captured.out and "body" in captured.out
