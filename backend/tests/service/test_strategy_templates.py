from src.service import strategy_templates


def test_strategy_templates_registry_and_lookup():
    templates = strategy_templates.get_all_templates()
    assert isinstance(templates, list)
    assert any(t["id"] == "ema_cross" for t in templates)

    detail = strategy_templates.get_template_by_id("ema_cross")
    assert detail is not None
    assert detail["id"] == "ema_cross"
    assert "code" in detail

    assert strategy_templates.get_template_by_id("missing") is None

