from agents.skills.accelerator import accelerator_program_summary, generate_accelerator_plan


def test_accelerator_summary():
    apps = {"a1": {"focus": "tech"}, "a2": {"focus": "tech"}, "a3": {"focus": "edu"}}
    out = accelerator_program_summary(apps)
    assert out["total_applicants"] == 3


def test_generate_accelerator_plan_fallback():
    out = generate_accelerator_plan({})
    assert isinstance(out, str)
    assert "Select top applicants" in out or len(out) > 0
