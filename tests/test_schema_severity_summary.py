import pytest

from driftlens.schema.severity_summary import (
    overall_severity,
    severity_counts,
    severity_rank,
)


def test_severity_counts_returns_all_ordered_keys_with_zero_counts() -> None:
    classified_changes = [
        {"path": "price", "severity": "high"},
        {"path": "description", "severity": "medium"},
        {"path": "tags", "severity": "high"},
    ]

    counts = severity_counts(classified_changes)

    assert counts == {"high": 2, "medium": 1, "low": 0}
    assert list(counts) == ["high", "medium", "low"]


def test_severity_counts_rejects_unknown_severity() -> None:
    classified_changes = [{"path": "price", "severity": "critical"}]

    with pytest.raises(ValueError):
        severity_counts(classified_changes)


def test_overall_severity_returns_high_when_any_high_count_exists() -> None:
    counts = {"high": 1, "medium": 2, "low": 3}

    assert overall_severity(counts) == "high"


def test_overall_severity_returns_medium_without_high() -> None:
    counts = {"high": 0, "medium": 1, "low": 3}

    assert overall_severity(counts) == "medium"


def test_overall_severity_returns_low_when_only_low_exists() -> None:
    counts = {"high": 0, "medium": 0, "low": 1}

    assert overall_severity(counts) == "low"


def test_overall_severity_returns_none_when_all_counts_are_zero() -> None:
    counts = {"high": 0, "medium": 0, "low": 0}

    assert overall_severity(counts) == "none"


def test_severity_rank_returns_expected_rank_mapping_deterministically() -> None:
    expected = {"high": 0, "medium": 1, "low": 2}

    assert severity_rank() == expected
    assert severity_rank() == expected
