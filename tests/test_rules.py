import pytest
from pydantic import ValidationError

from wedding_venue_finder.rules import HardRule, Preference, load_rules


def test_the_real_rules_file_loads():
    rules = load_rules()
    assert rules.guests > 0
    assert rules.hard, "there should be at least one hard rule"


def test_a_misspelt_key_is_an_error():
    row = {"field": "outside_catering_allowed", "prefernce": True, "weight": 2, "source": "page"}
    with pytest.raises(ValidationError):
        Preference.model_validate(row)


def test_an_unknown_operator_is_an_error():
    row = {"field": "seated_capacity", "op": "=>", "value": 175, "source": "page"}
    with pytest.raises(ValidationError):
        HardRule.model_validate(row)
