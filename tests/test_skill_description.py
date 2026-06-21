from repo_to_skill.skillgen.renderer import (
    _bundle_skill_description,
    _callable_skill_description,
    _goal_intent,
)


def test_goal_intent_lowercases_and_prefixes() -> None:
    assert _goal_intent("Calculate employee workload") == "you need to calculate employee workload"


def test_goal_intent_strips_trailing_period() -> None:
    assert _goal_intent("Onboard a new hire.") == "you need to onboard a new hire"


def test_goal_intent_falls_back_when_generic() -> None:
    assert _goal_intent("") == "you need these live capabilities"
    assert _goal_intent("Selected callable interfaces.") == "you need these live capabilities"


def test_bundle_description_is_trigger_shaped() -> None:
    text = _bundle_skill_description("acme", "calculate employee workload", 3)
    assert text.startswith("Use when you need to calculate employee workload")
    assert "acme" in text
    assert "3 callable tools" in text


def test_bundle_description_singular_tool() -> None:
    text = _bundle_skill_description("acme", "do one thing", 1)
    assert "1 callable tool" in text
    assert "callable tools" not in text


def test_callable_description_is_trigger_shaped() -> None:
    text = _callable_skill_description("acme", "WorkController.calculate", "POST", "/api/work/calculate")
    assert text.startswith("Use when you need the live result of acme's WorkController.calculate")
    assert "POST /api/work/calculate" in text
