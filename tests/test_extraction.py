import json

from wedding_venue_finder.extraction import EXTRACTION_PATH, ai_extract_schema, render
from wedding_venue_finder.schema import VenueFacts


def test_every_venue_fact_is_in_the_schema():
    assert set(ai_extract_schema()) == set(VenueFacts.model_fields)


def test_types_are_mapped():
    schema = ai_extract_schema()
    assert schema["max_guests"]["type"] == "integer"
    assert schema["has_pool"]["type"] == "boolean"
    assert schema["curfew"]["type"] == "string"
    assert schema["venue_hire"]["type"] == "object"
    assert schema["venue_hire"]["properties"]["currency"] == {"type": "enum", "labels": ["EUR", "GBP"]}


def test_every_field_has_a_description():
    assert all(field.get("description") for field in ai_extract_schema().values())


def test_safe_to_put_inside_a_sql_string():
    # The notebook puts the schema and instructions inside '...' in SQL.
    text = json.dumps(json.loads(render()), ensure_ascii=False)
    assert "'" not in text
    assert "\\" not in text


def test_the_committed_file_is_up_to_date():
    assert EXTRACTION_PATH.read_text() == render(), "run: uv run write-extraction"
