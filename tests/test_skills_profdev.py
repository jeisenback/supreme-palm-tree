from agents.skills.professional_development import suggest_training_programs, generate_profdev_plan


def test_suggest_training_programs_basic():
    skills = {"python": 5, "fundraising": 2, "governance": 3, "communications": 4}
    out = suggest_training_programs(skills)
    assert isinstance(out, dict)
    assert "recommendations" in out


def test_generate_profdev_plan_fallback():
    skills = {"python": 5, "fundraising": 2}
    plan = generate_profdev_plan(skills)
    assert isinstance(plan, str)
    assert len(plan) > 0
