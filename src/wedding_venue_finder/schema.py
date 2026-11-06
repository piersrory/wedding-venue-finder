"""VenueFacts: what the model extracts from a venue's pages.

Three rules, all learned from labelling by hand:
1. Every fact can be unknown (value None). A blank is a real answer.
2. Every known fact comes with a quote: the exact words on the page, so code
   can check they are really there.
3. The model copies, code calculates. Prices keep the currency the page used,
   and the curfew stays a clock time; code converts both (see convert.py).

The field descriptions are sent to the model as part of the extraction schema,
so they are written as instructions. No apostrophes: they go inside a SQL string.
"""

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from wedding_venue_finder.convert import NO_CURFEW, curfew_hours_past_midnight  # noqa: F401
from wedding_venue_finder.rules import StrictModel

# "02:00" or "none" (the page says there's no curfew)
Curfew = Annotated[str, StringConstraints(pattern=r"^(([01]\d|2[0-3]):[0-5]\d|none)$")]


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

    max_guests: Fact[int] = Field(
        description="Largest number of wedding guests the venue says it can host, "
        "for example from up to 250 guests. A whole number."
    )
    live_band_allowed: Fact[bool] = Field(
        description="true if the page says live bands or live music are allowed; "
        "false if it says they are not."
    )
    open_bar_available: Fact[bool] = Field(
        description="true if an open bar or drinks package is offered or included; "
        "false if the page says there is none."
    )
    has_pool: Fact[bool] = Field(
        description="true if the venue has a swimming pool; "
        "false if the page says there is no pool."
    )
    sleeps_on_site: Fact[int] = Field(
        description="Number of guests who can sleep at the venue (sleeps N). "
        "0 if the page says there is no on-site accommodation."
    )
    bring_your_own_drinks_allowed: Fact[bool] = Field(
        description="true if couples may bring their own alcohol or drinks; "
        "false if the page says they may not."
    )
    outside_catering_allowed: Fact[bool] = Field(
        description="true if external caterers are allowed; "
        "false if catering is in-house or exclusive only."
    )
    curfew: Fact[Curfew] = Field(
        description="Time the music or party must end, as 24-hour HH:MM (2am is 02:00). "
        "none if the page says there is no curfew."
    )
    venue_hire: Fact[Money] = Field(
        description="Venue hire or exclusive-use fee as written, with the currency of its symbol "
        "(EUR for the euro sign, GBP for the pound sign). Do not convert."
    )
    catering_pp: Fact[Money] = Field(
        description="Catering or menu price per person as written (the lowest if several), "
        "with its currency. Do not convert."
    )
    bar_pp: Fact[Money] = Field(
        description="Separate bar or drinks package price per person, with its currency. "
        "0 if the page says drinks are included in the menu price."
    )
