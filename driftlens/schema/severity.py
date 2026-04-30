def classify_severity(change: dict) -> str:
    """Return deterministic severity for a schema diff change."""
    change_type = change["change_type"]

    if change_type in {"field_removed", "type_changed"}:
        return "high"

    if change_type == "field_added":
        return "low"

    if change_type == "nullability_changed":
        if change["previous"] is False and change["current"] is True:
            return "medium"
        if change["previous"] is True and change["current"] is False:
            return "low"
        raise ValueError(f"Unsupported nullability transition: {change!r}")

    raise ValueError(f"Unknown change_type: {change_type}")


def classify_changes(changes: list[dict]) -> list[dict]:
    """Return schema changes with severity without mutating the input."""
    classified_changes = []

    for change in changes:
        classified_change = dict(change)
        classified_change["severity"] = classify_severity(change)
        classified_changes.append(classified_change)

    return classified_changes
