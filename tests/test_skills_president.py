from agents.skills.president import generate_agenda


def test_generate_agenda_basic():
    notes = {"title": "April Board", "date": "2026-04-01", "summary": "Quarterly planning."}
    md = generate_agenda(notes)
    assert "# Agenda — April Board" in md
    assert "**Date:** 2026-04-01" in md
    assert "Quarterly planning." in md
    assert "## Proposed Agenda" in md
