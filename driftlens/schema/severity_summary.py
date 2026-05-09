SEVERITIES = ("high", "medium", "low")


def severity_counts(classified_changes: list[dict]) -> dict[str, int]:
    """Return ordered severity counts for classified schema changes."""
    counts = {severity: 0 for severity in SEVERITIES}

    for change in classified_changes:
        severity = change["severity"]
        if severity not in counts:
            raise ValueError(f"Unknown severity: {severity}")
        counts[severity] += 1

    return counts


def overall_severity(counts: dict[str, int]) -> str:
    """Return the highest present severity, or none when there is no drift."""
    for severity in SEVERITIES:
        if counts[severity] > 0:
            return severity

    return "none"


def severity_rank() -> dict[str, int]:
    """Return deterministic rank values for severity ordering."""
    return {severity: index for index, severity in enumerate(SEVERITIES)}
