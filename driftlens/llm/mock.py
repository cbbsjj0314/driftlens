from driftlens.llm.representative import representative_changes


SEVERITIES = ("high", "medium", "low")


def _severity_counts(classified_changes: list[dict]) -> dict[str, int]:
    counts = {severity: 0 for severity in SEVERITIES}

    for change in classified_changes:
        severity = change["severity"]
        if severity not in counts:
            raise ValueError(f"Unknown severity: {severity}")
        counts[severity] += 1

    return counts


def _overall_severity(severity_counts: dict[str, int]) -> str:
    for severity in SEVERITIES:
        if severity_counts[severity] > 0:
            return severity

    return "none"


def _change_types(classified_changes: list[dict]) -> list[str]:
    seen = set()
    ordered_change_types = []

    for change in classified_changes:
        change_type = change["change_type"]
        if change_type not in seen:
            seen.add(change_type)
            ordered_change_types.append(change_type)

    return ordered_change_types


def _impacts(change_types: list[str]) -> list[str]:
    impacts = []

    if "field_removed" in change_types or "type_changed" in change_types:
        impacts.append(
            "Parser, normalization, and table mapping assumptions should be reviewed."
        )
    if "field_added" in change_types:
        impacts.append("New field mapping should be reviewed before downstream use.")
    if "nullability_changed" in change_types:
        impacts.append("Null handling and NOT NULL constraints should be reviewed.")

    return impacts


def _normalization_suggestions(change_types: list[str]) -> list[str]:
    suggestions = []

    if "field_removed" in change_types or "type_changed" in change_types:
        suggestions.append(
            "Check parser and normalization logic for removed fields or changed types."
        )
    if "field_added" in change_types:
        suggestions.append("Decide whether new fields need explicit normalization mapping.")
    if "nullability_changed" in change_types:
        suggestions.append("Check null handling before applying NOT NULL constraints.")

    return suggestions


def _test_case_suggestions(change_count: int, change_types: list[str]) -> list[str]:
    if change_count == 0:
        return ["Keep a no-drift regression test for unchanged previous/current fixtures."]

    suggestions = [
        "Add a previous/current fixture regression test for the classified diff."
    ]

    if change_types:
        suggestions.append("Add changed field coverage for parser and normalization paths.")

    return suggestions


class MockLLMProvider:
    """Return deterministic mock analysis for classified schema changes."""

    def analyze_diff(
        self,
        *,
        previous_schema_hash: str,
        current_schema_hash: str,
        classified_changes: list[dict],
    ) -> dict:
        severity_counts = _severity_counts(classified_changes)
        overall_severity = _overall_severity(severity_counts)
        change_types = _change_types(classified_changes)
        change_count = len(classified_changes)

        return {
            "provider": "mock",
            "previous_schema_hash": previous_schema_hash,
            "current_schema_hash": current_schema_hash,
            "change_count": change_count,
            "severity_counts": severity_counts,
            "overall_severity": overall_severity,
            "operator_summary": (
                f"Mock analysis found {change_count} classified schema changes "
                f"with overall severity {overall_severity}."
            ),
            "representative_changes": representative_changes(classified_changes),
            "impacts": _impacts(change_types),
            "normalization_suggestions": _normalization_suggestions(change_types),
            "test_case_suggestions": _test_case_suggestions(
                change_count,
                change_types,
            ),
        }
