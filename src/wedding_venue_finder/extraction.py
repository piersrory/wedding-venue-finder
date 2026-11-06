"""Turn VenueFacts into the schema Databricks' ai_extract expects.

VenueFacts stays the single source of truth: this module writes
data/extraction.json from it, and a test fails if the file is out of date.
Run it with:  uv run write-extraction
"""

import json
from pathlib import Path
from typing import Annotated, get_args, get_origin

from pydantic import BaseModel

from wedding_venue_finder.schema import Money, VenueFacts

EXTRACTION_PATH = Path(__file__).parents[2] / "data" / "extraction.json"

# Bump this when the schema or instructions change, so results land in a new
# table (extracted_v2, ...) and can be compared with the old one.
VERSION = "v1"

INSTRUCTIONS = (
    "You are reading saved web pages about ONE wedding venue in Spain. "
    "The pages may also mention other, similar venues: ignore them. "
    "Only fill a field if the text states it; otherwise leave it null. "
    "Never guess, and never infer from photos. "
    "Copy prices as written, in the currency shown; do not convert. "
    "Numbers may use a comma as the decimal separator: 148,45 means 148.45."
)

_SIMPLE_TYPES = {int: "integer", float: "number", bool: "boolean", str: "string"}


def _field_type(fact_class: type[BaseModel]) -> type:
    """Fact[int] -> int, Fact[Curfew] -> str, Fact[Money] -> Money."""
    (inner,) = fact_class.__pydantic_generic_metadata__["args"]
    if get_origin(inner) is Annotated:
        inner = get_args(inner)[0]
    return inner


def _money_schema(description: str) -> dict:
    currencies = list(get_args(Money.model_fields["currency"].annotation))
    return {
        "type": "object",
        "description": description,
        "properties": {
            "amount": {"type": "number"},
            "currency": {"type": "enum", "labels": currencies},
        },
    }


def ai_extract_schema() -> dict:
    """VenueFacts as an ai_extract (version 2.1) advanced schema."""
    schema = {}
    for name, field in VenueFacts.model_fields.items():
        inner = _field_type(field.annotation)
        if inner is Money:
            schema[name] = _money_schema(field.description)
        else:
            schema[name] = {"type": _SIMPLE_TYPES[inner], "description": field.description}
    return schema


def extraction_config() -> dict:
    return {"version": VERSION, "instructions": INSTRUCTIONS, "schema": ai_extract_schema()}


def render() -> str:
    return json.dumps(extraction_config(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    EXTRACTION_PATH.write_text(render())
    print(f"wrote {EXTRACTION_PATH}")
