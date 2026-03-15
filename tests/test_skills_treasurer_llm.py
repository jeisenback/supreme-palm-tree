from agents.skills.treasurer import summarize_finances, summarize_finances_with_llm
from agents.llm_adapter import NoOpAdapter


def test_treasurer_llm_fallback():
    csv_text = "category,amount\nDonations,1000\nExpenses,250\n"
    out = summarize_finances_with_llm(csv_text, adapter=NoOpAdapter())
    assert "Grand Total" in out
    assert "Donations" in out
