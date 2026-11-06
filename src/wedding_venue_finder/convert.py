"""Conversions done in code, never by the model. Standard library only."""

NO_CURFEW = 32.0  # hours past midnight; matches the labels


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


def to_eur(amount: float, currency: str, eur_to_gbp: float) -> float:
    """Convert a price to euros. eur_to_gbp is how many pounds one euro buys."""
    if currency == "EUR":
        return amount
    if currency == "GBP":
        return amount / eur_to_gbp
    raise ValueError(f"unknown currency: {currency}")
