import pytest

from driftlens.schema.diff import diff_schemas
from driftlens.schema.severity import classify_changes, classify_severity


def field(path: str, types: list[str], nullable: bool = False) -> dict:
    return {"path": path, "types": types, "nullable": nullable}


def schema(fields: list[dict]) -> dict:
    return {"fields": fields}


def test_classify_severity_returns_high_for_field_removed() -> None:
    change = {"change_type": "field_removed"}

    assert classify_severity(change) == "high"


def test_classify_severity_returns_high_for_type_changed() -> None:
    change = {"change_type": "type_changed"}

    assert classify_severity(change) == "high"


def test_classify_severity_returns_low_for_field_added() -> None:
    change = {"change_type": "field_added"}

    assert classify_severity(change) == "low"


def test_classify_severity_returns_medium_when_field_becomes_nullable() -> None:
    change = {
        "change_type": "nullability_changed",
        "previous": False,
        "current": True,
    }

    assert classify_severity(change) == "medium"


def test_classify_severity_returns_low_when_field_becomes_non_nullable() -> None:
    change = {
        "change_type": "nullability_changed",
        "previous": True,
        "current": False,
    }

    assert classify_severity(change) == "low"


def test_classify_severity_rejects_invalid_nullability_transition() -> None:
    change = {
        "change_type": "nullability_changed",
        "previous": False,
        "current": False,
    }

    with pytest.raises(ValueError):
        classify_severity(change)


def test_classify_severity_rejects_unknown_change_type() -> None:
    change = {"change_type": "renamed_field"}

    with pytest.raises(ValueError):
        classify_severity(change)


def test_classify_changes_adds_severity_to_new_list_and_dicts() -> None:
    changes = [
        {
            "change_type": "field_added",
            "path": "name",
            "previous": None,
            "current": field("name", ["string"]),
        },
        {
            "change_type": "type_changed",
            "path": "price",
            "previous": ["integer"],
            "current": ["object"],
        },
    ]

    classified_changes = classify_changes(changes)

    assert classified_changes == [
        {
            "change_type": "field_added",
            "path": "name",
            "previous": None,
            "current": field("name", ["string"]),
            "severity": "low",
        },
        {
            "change_type": "type_changed",
            "path": "price",
            "previous": ["integer"],
            "current": ["object"],
            "severity": "high",
        },
    ]
    assert classified_changes is not changes
    assert classified_changes[0] is not changes[0]
    assert classified_changes[1] is not changes[1]


def test_classify_changes_does_not_mutate_input_list_or_dicts() -> None:
    changes = [
        {
            "change_type": "field_added",
            "path": "name",
            "previous": None,
            "current": field("name", ["string"]),
        }
    ]
    original_changes = [dict(change) for change in changes]

    classify_changes(changes)

    assert changes == original_changes
    assert "severity" not in changes[0]


def test_classify_changes_accepts_diff_schemas_output_without_mutating_it() -> None:
    previous = schema(
        [
            field("description", ["string"]),
            field("price", ["integer"]),
        ]
    )
    current = schema(
        [
            field("description", ["null", "string"], nullable=True),
            field("price", ["object"]),
        ]
    )

    changes = diff_schemas(previous, current)
    classified_changes = classify_changes(changes)

    assert all("severity" not in change for change in changes)
    assert classified_changes == [
        {
            "change_type": "nullability_changed",
            "path": "description",
            "previous": False,
            "current": True,
            "severity": "medium",
        },
        {
            "change_type": "type_changed",
            "path": "price",
            "previous": ["integer"],
            "current": ["object"],
            "severity": "high",
        },
    ]
