from agents.skills.president import generate_agenda, generate_agenda_with_llm
from agents.llm_adapter import NoOpAdapter


def test_generate_agenda_with_noop_adapter_falls_back():
    notes = {"title": "April Board", "date": "2026-04-01", "summary": "Quarterly planning."}
    md1 = generate_agenda(notes)
    md2 = generate_agenda_with_llm(notes, adapter=NoOpAdapter())
    assert md1.splitlines()[0] == md2.splitlines()[0]
