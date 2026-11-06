"""VenueFacts: what the model extracts from a venue's pages.

Three rules, all learned from labelling by hand:
1. Every fact can be unknown (value None). A blank is a real answer.
2. Every known fact comes with a quote: the exact words on the page, so code
   can check they are really there.
3. The model copies, code calculates. Prices keep the currency the page used,
   and the curfew stays a clock time; code converts both.
"""

from typing import Annotated, Literal

from pydantic import StringConstraints, model_validator

from wedding_venue_finder.rules import StrictModel

# "02:00" or "none" (the page says there's no curfew)
Curfew = Annotated[str, StringConstraints(pattern=r"^(([01]\d|2[0-3]):[0-5]\d|none)$")]

NO_CURFEW = 32.0  # hours past midnight; matches the labels


class Fact[T](StrictModel):
    """One fact from the page: its value, and the words it came from."""

    value: T | None = None
    quote: str | None = None

    @model_validator(mode="after")
    def quote_goes_with_value(self):
        if self.value is not None and not self.quote:
            raise ValueError("a known value needs a quote from the page")
        if self.value is None and self.quote:
            raise ValueError("a quote with no value: either fill in the value or drop the quote")
        return self


class Money(StrictModel):
    amount: float
    currency: Literal["EUR", "GBP"]


class VenueFacts(StrictModel):
    """Everything rules.yaml needs from the page, plus the price pieces for the total."""

    max_guests: Fact[int]
    live_band_allowed: Fact[bool]
    open_bar_available: Fact[bool]
    has_pool: Fact[bool]
    sleeps_on_site: Fact[int]
    bring_your_own_drinks_allowed: Fact[bool]
    outside_catering_allowed: Fact[bool]
    curfew: Fact[Curfew]
    venue_hire: Fact[Money]
    catering_pp: Fact[Money]
    bar_pp: Fact[Money]


def curfew_hours_past_midnight(curfew: str) -> float:
    """'02:00' -> 26.0, '23:30' -> 23.5, 'none' -> 32.0.

    Times before midday are taken as after midnight: a wedding curfew of
    "02:00" means 2am the next morning, not 2am before the wedding.
    """
    if curfew == "none":
        return NO_CURFEW
    hours, minutes = (int(part) for part in curfew.split(":"))
    if hours < 12:
        hours += 24
    return hours + minutes / 60
