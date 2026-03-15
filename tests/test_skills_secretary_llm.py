from agents.skills.secretary import extract_action_items, extract_action_items_with_llm
from agents.llm_adapter import NoOpAdapter


def test_secretary_llm_falls_back_to_heuristic():
    notes = {"text": "Action: Reach out to sponsor by Alice due 2026-04-20"}
    a = extract_action_items(notes)
    b = extract_action_items_with_llm(notes, adapter=NoOpAdapter())
    assert a == b
