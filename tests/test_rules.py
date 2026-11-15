import pytest
from pydantic import ValidationError

from wedding_venue_finder.rules import RULES_PATH, HardRule, Preference, load_rules, rules_path


def test_the_public_rules_file_loads():
    rules = load_rules(RULES_PATH)
    assert rules.guests > 0
    assert rules.hard, "there should be at least one hard rule"


def test_the_public_budget_is_left_out():
    rules = load_rules(RULES_PATH)
    budget = next(rule for rule in rules.hard if rule.field == "total_cost_gbp")
    assert budget.value is None


def test_local_rules_win_when_present(tmp_path):
    (tmp_path / "rules.yaml").write_text("public")
    assert rules_path(tmp_path) == tmp_path / "rules.yaml"
    (tmp_path / "rules.local.yaml").write_text("mine")
    assert rules_path(tmp_path) == tmp_path / "rules.local.yaml"


def test_a_misspelt_key_is_an_error():
    row = {"field": "outside_catering_allowed", "prefernce": True, "weight": 2, "source": "page"}
    with pytest.raises(ValidationError):
        Preference.model_validate(row)


def test_an_unknown_operator_is_an_error():
    row = {"field": "seated_capacity", "op": "=>", "value": 175, "source": "page"}
    with pytest.raises(ValidationError):
        HardRule.model_validate(row)
