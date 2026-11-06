import pytest

from wedding_venue_finder.evaluate import number_forms, number_in_quotes, outcome, score_venue

RATE = 0.83


@pytest.mark.parametrize(
    ("field", "label", "value", "expected"),
    [
        ("max_guests", "200", 200, "correct"),
        ("max_guests", "200", 220, "wrong"),
        ("max_guests", None, None, "both_unknown"),
        ("max_guests", "null", None, "both_unknown"),
        ("live_band_allowed", None, True, "invented"),
        ("bring_your_own_drinks_allowed", "false", None, "missed"),
        ("has_pool", "false", False, "correct"),
        ("curfew", "32", "none", "correct"),
        ("curfew", "27", "03:00", "correct"),
        ("curfew", "26", "01:00", "wrong"),
        ("catering_pp", "148.45", (148.45, "EUR"), "correct"),
        ("catering_pp", "148.45", (131, "EUR"), "wrong"),
        ("venue_hire", "13253", (11000, "GBP"), "correct"),  # La Farinera: £ converted
        ("venue_hire", "13253", (11000, "EUR"), "wrong"),  # the mistake we nearly made
        ("venue_hire", "9900", (9900, None), "wrong"),  # an amount with no currency
        ("bar_pp", "0", (0, "EUR"), "correct"),
    ],
)
def test_outcomes(field, label, value, expected):
    assert outcome(field, label, value, RATE) == expected


def test_number_forms_cover_spanish_and_english_writing():
    assert number_forms(9900) == ["9900", "9,900", "9.900", "9 900"]
    assert number_forms(148.45) == ["148.45", "148,45"]


def test_number_in_quotes():
    assert number_in_quotes("venue_hire", (9900, "EUR"), ["Price From €9,900"]) is True
    assert number_in_quotes("venue_hire", (4250, "EUR"), ["Price From €9,900"]) is False
    assert number_in_quotes("has_pool", True, ["pool"]) is None


def test_score_venue_uses_citations_as_quotes():
    text = "Weddings up to 250 Guests. Price From €9,900."
    result = {
        "response": {
            "max_guests": {"citation_ids": [0], "value": 250},
            "venue_hire": {
                "amount": {"citation_ids": [1], "value": 4250},
                "currency": {"citation_ids": [1], "value": "EUR"},
            },
        },
        "metadata": {"citations": [{"id": 0, "start": 0, "stop": 25}, {"id": 1, "start": 27, "stop": 45}]},
    }
    rows = {r["field"]: r for r in score_venue("x", {"max_guests": "250", "venue_hire_eur": "9900"}, result, text, RATE)}
    assert rows["max_guests"]["outcome"] == "correct"
    assert rows["max_guests"]["quote"] == "Weddings up to 250 Guests"
    assert rows["venue_hire"]["outcome"] == "wrong"
    assert rows["venue_hire"]["number_in_quote"] is False  # 4250 isn't in what it cited
