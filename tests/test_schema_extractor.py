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
