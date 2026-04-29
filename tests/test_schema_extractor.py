import json
from pathlib import Path

from driftlens.schema.extractor import extract_schema


def test_extract_schema_from_flat_steam_appdetails_fixture() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "steam_appdetails_v1.json"
    data = json.loads(fixture_path.read_text())

    schema = extract_schema(data)

    fields_by_path = {field["path"]: field for field in schema["fields"]}
    assert fields_by_path == {
        "appid": {"path": "appid", "types": ["integer"], "nullable": False},
        "name": {"path": "name", "types": ["string"], "nullable": False},
        "price": {"path": "price", "types": ["integer"], "nullable": False},
        "currency": {"path": "currency", "types": ["string"], "nullable": False},
    }


def test_extract_schema_from_nested_steam_appdetails_fixture() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "steam_appdetails_nested_v1.json"
    data = json.loads(fixture_path.read_text())

    schema = extract_schema(data)

    assert schema["fields"] == [
        {"path": "appid", "types": ["integer"], "nullable": False},
        {"path": "name", "types": ["string"], "nullable": False},
        {"path": "price", "types": ["object"], "nullable": False},
        {"path": "price.currency", "types": ["string"], "nullable": False},
        {"path": "price.final", "types": ["integer"], "nullable": False},
    ]


def test_extract_schema_from_array_steam_appdetails_fixture() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "steam_appdetails_arrays_v1.json"
    data = json.loads(fixture_path.read_text())

    schema = extract_schema(data)

    assert schema["fields"] == [
        {"path": "appid", "types": ["integer"], "nullable": False},
        {"path": "genres", "types": ["array"], "nullable": False},
        {"path": "genres[]", "types": ["object"], "nullable": False},
        {"path": "genres[].description", "types": ["string"], "nullable": False},
        {"path": "genres[].id", "types": ["integer"], "nullable": False},
        {"path": "metadata", "types": ["object"], "nullable": False},
        {
            "path": "metadata.supported_languages",
            "types": ["array"],
            "nullable": False,
        },
        {
            "path": "metadata.supported_languages[]",
            "types": ["string"],
            "nullable": False,
        },
        {
            "path": "mixed_values",
            "types": ["array"],
            "nullable": False,
        },
        {
            "path": "mixed_values[]",
            "types": ["integer", "null", "string"],
            "nullable": True,
        },
        {"path": "screenshots", "types": ["array"], "nullable": False},
        {"path": "tags", "types": ["array"], "nullable": False},
        {"path": "tags[]", "types": ["string"], "nullable": False},
    ]
