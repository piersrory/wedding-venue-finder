"""Score ai_extract results against the hand labels. Standard library only.

Each (venue, field) pair gets one outcome:
  correct       both known, and they agree
  wrong         both known, and they disagree
  missed        the label has a value, the model said unknown
  invented      the label is blank (page doesn't say), the model gave a value
  both_unknown  neither has a value: agreement on "not stated"
"""

from wedding_venue_finder.convert import curfew_hours_past_midnight, to_eur

BOOL_FIELDS = [
    "live_band_allowed",
    "open_bar_available",
    "has_pool",
    "bring_your_own_drinks_allowed",
    "outside_catering_allowed",
]
INT_FIELDS = ["max_guests", "sleeps_on_site"]
MONEY_FIELDS = {"venue_hire": "venue_hire_eur", "catering_pp": "catering_pp_eur", "bar_pp": "bar_pp_eur"}
CURFEW_LABEL = "curfew_hours_past_midnight"

FIELDS = INT_FIELDS + BOOL_FIELDS + ["curfew"] + list(MONEY_FIELDS)

PRICE_TOLERANCE = 0.01  # 1%, so currency conversion rounding still counts as correct


def _blank(value) -> bool:
    return value is None or str(value).strip() in ("", "null")


def extracted_value(response: dict, field: str):
    """The model's value for a field, or None. Money comes back as (amount, currency)."""
    item = response.get(field) or {}
    if field in MONEY_FIELDS:
        amount = (item.get("amount") or {}).get("value")
        currency = (item.get("currency") or {}).get("value")
        return None if amount is None else (amount, currency)
    return item.get("value")


def citation_ids(response: dict, field: str) -> list[int]:
    item = response.get(field) or {}
    if field in MONEY_FIELDS:
        item = item.get("amount") or {}
    return item.get("citation_ids") or []


def quotes(result: dict, text: str, field: str) -> list[str]:
    """The cited spans of the venue's text for a field."""
    spans = {c["id"]: (c["start"], c["stop"]) for c in result.get("metadata", {}).get("citations", [])}
    return [text[spans[i][0] : spans[i][1]] for i in citation_ids(result["response"], field) if i in spans]


def _agree(field: str, label: str, value, eur_to_gbp: float) -> bool:
    if field in BOOL_FIELDS:
        return (label.strip().lower() == "true") == bool(value)
    if field in INT_FIELDS:
        return int(float(label)) == int(value)
    if field == "curfew":
        return abs(float(label) - curfew_hours_past_midnight(value)) < 0.01
    amount, currency = value
    if currency is None:
        return False
    expected = float(label)
    got = to_eur(float(amount), currency, eur_to_gbp)
    if expected == 0:
        return got == 0
    return abs(got - expected) / expected <= PRICE_TOLERANCE


def outcome(field: str, label, value, eur_to_gbp: float) -> str:
    if _blank(label) and value is None:
        return "both_unknown"
    if _blank(label):
        return "invented"
    if value is None:
        return "missed"
    return "correct" if _agree(field, str(label), value, eur_to_gbp) else "wrong"


def label_column(field: str) -> str:
    if field == "curfew":
        return CURFEW_LABEL
    return MONEY_FIELDS.get(field, field)


def number_forms(number: float) -> list[str]:
    """How a number might be written on a Spanish or English page: 9900, 9,900, 9.900, 148,45."""
    if float(number).is_integer():
        n = int(number)
        return [str(n), f"{n:,}", f"{n:,}".replace(",", "."), f"{n:,}".replace(",", " ")]
    return [f"{number:.2f}", f"{number:.2f}".replace(".", ",")]


def number_in_quotes(field: str, value, cited: list[str]) -> bool | None:
    """Is the extracted number actually written in the text the model cited?

    None when it can't be checked this way: yes/no fields, curfews, unknowns and zero.
    """
    if value is None or field in BOOL_FIELDS or field == "curfew":
        return None
    number = value[0] if field in MONEY_FIELDS else value
    if number == 0:
        return None
    return any(form in quote for form in number_forms(number) for quote in cited)


def score_venue(slug: str, label_row: dict, result: dict, text: str, eur_to_gbp: float) -> list[dict]:
    """One row per field: label, extracted value, outcome, and the evidence."""
    rows = []
    for field in FIELDS:
        label = label_row.get(label_column(field))
        value = extracted_value(result["response"], field)
        cited = quotes(result, text, field)
        rows.append(
            {
                "slug": slug,
                "field": field,
                "label": None if _blank(label) else str(label),
                "extracted": None if value is None else str(value),
                "outcome": outcome(field, label, value, eur_to_gbp),
                "number_in_quote": number_in_quotes(field, value, cited),
                "quote": " | ".join(q.replace("\n", " ") for q in cited),
            }
        )
    return rows
