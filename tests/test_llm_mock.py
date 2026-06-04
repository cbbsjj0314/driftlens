import copy
import json
from pathlib import Path

import pytest

from driftlens.llm.mock import MockLLMProvider
from driftlens.schema.diff import diff_schemas
from driftlens.schema.extractor import extract_schema
from driftlens.schema.hash import schema_hash
from driftlens.schema.severity import classify_changes


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def field(path: str, types: list[str], nullable: bool = False) -> dict:
    return {"path": path, "types": types, "nullable": nullable}


def analyze(classified_changes: list[dict]) -> dict:
    return MockLLMProvider().analyze_diff(
        previous_schema_hash="previous-hash",
        current_schema_hash="current-hash",
        classified_changes=classified_changes,
    )


def test_mock_llm_provider_returns_analysis_dict_with_required_keys() -> None:
    analysis = analyze(
        [
            {
                "change_type": "field_added",
                "path": "name",
                "previous": None,
                "current": field("name", ["string"]),
                "severity": "low",
            }
        ]
    )

    assert isinstance(analysis, dict)
    assert set(analysis) == {
        "provider",
        "previous_schema_hash",
        "current_schema_hash",
        "change_count",
        "severity_counts",
        "overall_severity",
        "operator_summary",
        "representative_changes",
        "impacts",
        "normalization_suggestions",
        "test_case_suggestions",
    }
    assert analysis["provider"] == "mock"
    assert analysis["previous_schema_hash"] == "previous-hash"
    assert analysis["current_schema_hash"] == "current-hash"
    assert analysis["change_count"] == 1
    assert set(analysis["severity_counts"]) == {"high", "medium", "low"}


def test_mock_llm_provider_returns_json_serializable_dict() -> None:
    analysis = analyze(
        [
            {
                "change_type": "field_removed",
                "path": "currency",
                "previous": field("currency", ["string"]),
                "current": None,
                "severity": "high",
            }
        ]
    )

    json.dumps(analysis)


def test_mock_llm_provider_returns_high_overall_severity() -> None:
    analysis = analyze(
        [
            {
                "change_type": "type_changed",
                "path": "price",
                "previous": ["integer"],
                "current": ["object"],
                "severity": "high",
            },
            {
                "change_type": "field_added",
                "path": "price.final",
                "previous": None,
                "current": field("price.final", ["integer"]),
                "severity": "low",
            },
        ]
    )

    assert analysis["overall_severity"] == "high"
    assert analysis["severity_counts"] == {"high": 1, "medium": 0, "low": 1}


def test_mock_llm_provider_returns_medium_overall_severity_when_only_medium() -> None:
    analysis = analyze(
        [
            {
                "change_type": "nullability_changed",
                "path": "description",
                "previous": False,
                "current": True,
                "severity": "medium",
            }
        ]
    )

    assert analysis["overall_severity"] == "medium"
    assert analysis["severity_counts"] == {"high": 0, "medium": 1, "low": 0}


def test_mock_llm_provider_returns_low_overall_severity_when_only_low() -> None:
    analysis = analyze(
        [
            {
                "change_type": "field_added",
                "path": "name",
                "previous": None,
                "current": field("name", ["string"]),
                "severity": "low",
            }
        ]
    )

    assert analysis["overall_severity"] == "low"
    assert analysis["severity_counts"] == {"high": 0, "medium": 0, "low": 1}


def test_mock_llm_provider_returns_none_overall_severity_when_no_changes() -> None:
    analysis = analyze([])

    assert analysis["change_count"] == 0
    assert analysis["overall_severity"] == "none"
    assert analysis["severity_counts"] == {"high": 0, "medium": 0, "low": 0}
    assert analysis["representative_changes"] == []


def test_mock_llm_provider_rejects_unknown_severity() -> None:
    with pytest.raises(ValueError, match="Unknown severity"):
        analyze(
            [
                {
                    "change_type": "field_added",
                    "path": "name",
                    "previous": None,
                    "current": field("name", ["string"]),
                    "severity": "critical",
                }
            ]
        )


def test_mock_llm_provider_suggests_parser_normalization_and_mapping_review() -> None:
    analysis = analyze(
        [
            {
                "change_type": "field_removed",
                "path": "currency",
                "previous": field("currency", ["string"]),
                "current": None,
                "severity": "high",
            },
            {
                "change_type": "type_changed",
                "path": "price",
                "previous": ["integer"],
                "current": ["object"],
                "severity": "high",
            },
        ]
    )

    assert (
        "Parser, normalization, and table mapping assumptions should be reviewed."
        in (analysis["impacts"])
    )
    assert (
        "Check parser and normalization logic for removed fields or changed types."
        in analysis["normalization_suggestions"]
    )


def test_mock_llm_provider_suggests_new_field_mapping_review() -> None:
    analysis = analyze(
        [
            {
                "change_type": "field_added",
                "path": "price.final",
                "previous": None,
                "current": field("price.final", ["integer"]),
                "severity": "low",
            }
        ]
    )

    assert (
        "New field mapping should be reviewed before downstream use."
        in (analysis["impacts"])
    )
    assert (
        "Decide whether new fields need explicit normalization mapping."
        in (analysis["normalization_suggestions"])
    )


def test_mock_llm_provider_suggests_null_handling_review() -> None:
    analysis = analyze(
        [
            {
                "change_type": "nullability_changed",
                "path": "description",
                "previous": False,
                "current": True,
                "severity": "medium",
            }
        ]
    )

    assert (
        "Null handling and NOT NULL constraints should be reviewed."
        in (analysis["impacts"])
    )
    assert (
        "Check null handling before applying NOT NULL constraints."
        in (analysis["normalization_suggestions"])
    )


def test_mock_llm_provider_returns_same_output_for_same_input() -> None:
    classified_changes = [
        {
            "change_type": "field_added",
            "path": "price.final",
            "previous": None,
            "current": field("price.final", ["integer"]),
            "severity": "low",
        },
        {
            "change_type": "nullability_changed",
            "path": "description",
            "previous": False,
            "current": True,
            "severity": "medium",
        },
    ]

    first_analysis = analyze(classified_changes)
    second_analysis = analyze(classified_changes)

    assert first_analysis == second_analysis
    assert first_analysis["impacts"] == second_analysis["impacts"]
    assert (
        first_analysis["normalization_suggestions"]
        == (second_analysis["normalization_suggestions"])
    )
    assert (
        first_analysis["test_case_suggestions"]
        == (second_analysis["test_case_suggestions"])
    )
    assert (
        first_analysis["representative_changes"]
        == (second_analysis["representative_changes"])
    )


def test_mock_llm_provider_returns_representative_changes_with_required_fields() -> (
    None
):
    analysis = analyze(
        [
            {
                "change_type": "field_added",
                "path": "price.final",
                "previous": None,
                "current": field("price.final", ["integer"]),
                "severity": "low",
            }
        ]
    )

    assert analysis["representative_changes"] == [
        {
            "severity": "low",
            "change_type": "field_added",
            "path": "price.final",
        }
    ]


def test_mock_llm_provider_orders_representative_changes_by_severity() -> None:
    analysis = analyze(
        [
            {
                "change_type": "field_added",
                "path": "new_field",
                "previous": None,
                "current": field("new_field", ["string"]),
                "severity": "low",
            },
            {
                "change_type": "field_removed",
                "path": "removed_field",
                "previous": field("removed_field", ["string"]),
                "current": None,
                "severity": "high",
            },
        ]
    )

    assert [change["severity"] for change in analysis["representative_changes"]] == [
        "high",
        "low",
    ]


def test_mock_llm_provider_limits_representative_changes() -> None:
    classified_changes = [
        {
            "change_type": "field_added",
            "path": f"field_{index}",
            "previous": None,
            "current": field(f"field_{index}", ["string"]),
            "severity": "low",
        }
        for index in range(6)
    ]

    analysis = analyze(classified_changes)

    assert len(analysis["representative_changes"]) == 5
    assert [change["path"] for change in analysis["representative_changes"]] == [
        "field_0",
        "field_1",
        "field_2",
        "field_3",
        "field_4",
    ]


def test_mock_llm_provider_includes_type_fields_for_type_changed() -> None:
    analysis = analyze(
        [
            {
                "change_type": "type_changed",
                "path": "required_age",
                "previous": ["string"],
                "current": ["integer"],
                "severity": "high",
            }
        ]
    )

    assert analysis["representative_changes"] == [
        {
            "severity": "high",
            "change_type": "type_changed",
            "path": "required_age",
            "previous_types": ["string"],
            "current_types": ["integer"],
        }
    ]


def test_mock_llm_provider_does_not_mutate_classified_changes() -> None:
    classified_changes = [
        {
            "change_type": "field_added",
            "path": "name",
            "previous": None,
            "current": field("name", ["string"]),
            "severity": "low",
        }
    ]
    original_changes = copy.deepcopy(classified_changes)

    analyze(classified_changes)

    assert classified_changes == original_changes


def test_mock_llm_provider_accepts_diff_and_classified_changes_output() -> None:
    previous_data = json.loads((FIXTURE_DIR / "steam_appdetails_v1.json").read_text())
    current_data = json.loads(
        (FIXTURE_DIR / "steam_appdetails_nested_v1.json").read_text()
    )
    previous_schema = extract_schema(previous_data)
    current_schema = extract_schema(current_data)
    changes = diff_schemas(previous_schema, current_schema)
    classified_changes = classify_changes(changes)

    analysis = MockLLMProvider().analyze_diff(
        previous_schema_hash=schema_hash(previous_schema),
        current_schema_hash=schema_hash(current_schema),
        classified_changes=classified_changes,
    )

    assert analysis["provider"] == "mock"
    assert analysis["change_count"] == len(classified_changes)
    assert analysis["overall_severity"] == "high"
