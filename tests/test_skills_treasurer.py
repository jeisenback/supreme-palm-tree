from agents.skills.treasurer import summarize_finances, balances_markdown


def test_summarize_finances_and_markdown():
    csv_text = "category,amount\nDonations,1000\nExpenses,250\nDonations,500\n"
    summary = summarize_finances(csv_text)
    assert summary["totals"]["Donations"] == 1500
    assert summary["totals"]["Expenses"] == 250
    md = balances_markdown(summary)
    assert "Financial Summary" in md
    assert "Donations" in md
    assert "Grand Total" in md
