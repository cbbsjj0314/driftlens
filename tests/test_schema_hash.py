import copy
import json
from pathlib import Path

from driftlens.schema.extractor import extract_schema
from driftlens.schema.hash import schema_hash


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def field(path: str, types: list[str], nullable: bool = False) -> dict:
    return {"path": path, "types": types, "nullable": nullable}


def schema(fields: list[dict]) -> dict:
    return {"fields": fields}


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_schema_hash_ignores_field_order() -> None:
    first = schema([field("appid", ["integer"]), field("name", ["string"])])
    second = schema([field("name", ["string"]), field("appid", ["integer"])])

    assert schema_hash(first) == schema_hash(second)


def test_schema_hash_ignores_type_order() -> None:
    first = schema([field("mixed_values[]", ["integer", "null", "string"], True)])
    second = schema([field("mixed_values[]", ["string", "integer", "null"], True)])

    assert schema_hash(first) == schema_hash(second)


def test_schema_hash_changes_when_path_changes() -> None:
    first = schema([field("price", ["integer"])])
    second = schema([field("price.final", ["integer"])])

    assert schema_hash(first) != schema_hash(second)


def test_schema_hash_changes_when_types_change() -> None:
    first = schema([field("price", ["integer"])])
    second = schema([field("price", ["object"])])

    assert schema_hash(first) != schema_hash(second)


def test_schema_hash_changes_when_nullable_changes() -> None:
    first = schema([field("description", ["string"])])
    second = schema([field("description", ["null", "string"], True)])

    assert schema_hash(first) != schema_hash(second)


def test_schema_hash_from_extracted_fixture_is_deterministic() -> None:
    data = load_fixture("steam_appdetails_arrays_v1.json")
    extracted_schema = extract_schema(data)

    assert schema_hash(extracted_schema) == schema_hash(extracted_schema)


def test_schema_hash_does_not_mutate_input_schema() -> None:
    observed_schema = schema(
        [
            field("name", ["string"]),
            field("mixed_values[]", ["string", "integer", "null"], True),
            field("appid", ["integer"]),
        ]
    )
    original_schema = copy.deepcopy(observed_schema)

    schema_hash(observed_schema)

    assert observed_schema == original_schema
