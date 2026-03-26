from agents.skills.operations import operations_checklist, generate_ops_plan


def test_operations_checklist_empty():
    out = operations_checklist({})
    assert isinstance(out, dict)
    assert "checklist" in out


def test_generate_ops_plan_fallback():
    out = generate_ops_plan({})
    assert isinstance(out, str)
    assert len(out) > 0
