from agents.skills.secretary import extract_action_items


def test_extract_action_items_from_list():
    notes = {"action_items": [{"owner": "Sam", "action": "Follow up with donor", "due": "2026-04-10"}]}
    items = extract_action_items(notes)
    assert items[0]["owner"] == "Sam"


def test_extract_action_items_from_text():
    notes = {"text": "Action: Reach out to sponsor by Alice due 2026-04-20"}
    items = extract_action_items(notes)
    assert len(items) == 1
    assert "Reach out to sponsor" in items[0]["action"]
    assert items[0]["due"] == "2026-04-20"
