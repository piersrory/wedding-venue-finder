import pytest
from pydantic import ValidationError

from wedding_venue_finder.schema import Fact, Money, VenueFacts, curfew_hours_past_midnight

UNKNOWN = {"value": None, "quote": None}


def blanes() -> dict:
    """El Convent Blanes as the model should extract it from the saved pages."""
    return {
        "max_guests": {"value": 200, "quote": "has a capacity for 200 guests"},
        "live_band_allowed": UNKNOWN,
        "open_bar_available": {"value": True, "quote": "Open bar throughout the celebration"},
        "has_pool": {"value": True, "quote": "a pool and lounge zone"},
        "sleeps_on_site": {"value": 0, "quote": "doesn't offer on-site accommodation"},
        "bring_your_own_drinks_allowed": UNKNOWN,
        "outside_catering_allowed": UNKNOWN,
        "curfew": {"value": "03:00", "quote": "Open bar service until 3:00 AM"},
        "venue_hire": UNKNOWN,
        "catering_pp": {
            "value": {"amount": 148.45, "currency": "EUR"},
            "quote": "Menu pricing starts at €148,45 per person",
        },
        "bar_pp": UNKNOWN,
    }


def test_a_full_venue_validates():
    facts = VenueFacts.model_validate(blanes())
    assert facts.max_guests.value == 200
    assert facts.catering_pp.value == Money(amount=148.45, currency="EUR")
    assert facts.venue_hire.value is None


def test_a_value_without_a_quote_is_rejected():
    with pytest.raises(ValidationError, match="needs a quote"):
        Fact[int].model_validate({"value": 200, "quote": None})


def test_a_quote_without_a_value_is_rejected():
    with pytest.raises(ValidationError, match="quote with no value"):
        Fact[int].model_validate({"value": None, "quote": "up to 600 guests"})


def test_prices_keep_their_currency():
    price = Fact[Money].model_validate(
        {"value": {"amount": 11000, "currency": "GBP"}, "quote": "Price From £11,000"}
    )
    assert price.value.currency == "GBP"


@pytest.mark.parametrize("bad", ["2am", "26:00", "2:00", "late"])
def test_a_curfew_must_be_a_clock_time_or_none(bad):
    with pytest.raises(ValidationError):
        VenueFacts.model_validate({**blanes(), "curfew": {"value": bad, "quote": "x"}})


@pytest.mark.parametrize(
    ("curfew", "hours"),
    [("23:00", 23.0), ("23:30", 23.5), ("00:30", 24.5), ("02:00", 26.0), ("03:00", 27.0), ("none", 32.0)],
)
def test_curfew_converts_to_hours_past_midnight(curfew, hours):
    assert curfew_hours_past_midnight(curfew) == hours


def test_the_schema_exports_as_json_schema():
    # Databricks' extraction needs a JSON schema; Pydantic writes it for us.
    schema = VenueFacts.model_json_schema()
    assert "curfew" in schema["properties"]
