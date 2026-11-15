"""The venue rules, loaded from data/rules.yaml and checked on the way in.

Every model forbids unknown keys, so a typo in the YAML is an error, not a
silently ignored setting.

The repo ships example figures, with the budget left out. Your own figures go
in data/rules.local.yaml (same shape, never committed), which is loaded
instead when it exists.
"""

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict

DATA_DIR = Path(__file__).parents[2] / "data"
RULES_PATH = DATA_DIR / "rules.yaml"  # the public example
LOCAL_RULES_NAME = "rules.local.yaml"  # your own figures, gitignored


def rules_path(data_dir: Path = DATA_DIR) -> Path:
    """Your local rules if you have them, otherwise the public example."""
    local = data_dir / LOCAL_RULES_NAME
    return local if local.exists() else data_dir / "rules.yaml"


class StrictModel(BaseModel):
    """Base for every rules model: an unknown key like "prefernce" is an error."""

    model_config = ConfigDict(extra="forbid")


class HardRule(StrictModel):
    """Fail one and the venue is out. Unknown is never a pass."""

    field: str  # which fact the rule checks
    op: Literal[">=", "<=", "=="]
    value: int | float | bool | None  # None = left out (the public budget), so not checked
    source: Literal["page", "computed"]
    airports: list[str] | None = None  # only the airport rule has it


class Preference(StrictModel):
    """Changes the ranking; never rules a venue out."""

    field: str
    better: Literal["lower", "higher", True]
    weight: int
    source: Literal["page", "computed"]
    target: float | None = None  # the point where more stops helping


class Ask(StrictModel):
    """A question only the venue can answer; goes into the enquiry email."""

    field: str
    value: date | bool


class Currency(StrictModel):
    eur_to_gbp: float
    rate_date: date


class RulesFile(StrictModel):
    """The whole of data/rules.yaml."""

    guests: int
    fixed_costs_gbp: dict[str, int]  # an open list of costs, summed
    currency: Currency  # exactly these keys; code relies on them
    hard: list[HardRule]
    preferences: list[Preference]
    ask: list[Ask]


def load_rules(path: Path | None = None) -> RulesFile:
    """Read the rules file and validate it. Raises if anything is wrong.

    With no path, uses rules_path(): your local figures if present.
    """
    path = path or rules_path()
    with path.open() as f:
        return RulesFile.model_validate(yaml.safe_load(f))
