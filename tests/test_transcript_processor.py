from agents.transcript_processor import parse_transcript_text


def test_parse_actions_and_research():
    txt = """
    Speaker A: Welcome everyone.
    Action: John to prepare the budget draft by next meeting.
    Research: Investigate local grant opportunities for Q3.

    - [ ] Follow up with vendor on pricing
    """
    res = parse_transcript_text(txt, use_llm=False)
    assert any("budget draft" in a.lower() for a in res["action_items"]) or len(res["action_items"]) >= 1
    assert any("grant" in r.lower() for r in res["research_items"]) or len(res["research_items"]) >= 1
    assert res["notes"]
