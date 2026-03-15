from agents.skills import (
    generate_fundraising_plan,
    generate_membership_insights,
    draft_announcement,
    generate_email_campaign,
)


def test_generate_fundraising_plan_basic():
    csv_text = "donor,amount\nAlice,100\nBob,50\nAlice,25\n"
    plan = generate_fundraising_plan(csv_text)
    assert isinstance(plan, str)
    assert len(plan) > 0


def test_generate_membership_insights_basic():
    csv_text = "member_id,joined_date,status\n1,2022-01-01,active\n2,2021-06-01,lapsed\n3,2023-02-01,active\n"
    insights = generate_membership_insights(csv_text)
    assert isinstance(insights, str)
    assert len(insights) > 0


def test_communications_draft_and_email():
    ctx = {"title": "Update", "audience": "members", "summary": "Brief update", "call_to_action": "Join us"}
    draft = draft_announcement(ctx)
    assert isinstance(draft, str)

    campaign = generate_email_campaign("Event", "members who joined in 2024")
    assert isinstance(campaign, dict)
    assert "subject" in campaign and "body" in campaign
