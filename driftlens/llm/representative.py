SEVERITIES = ("high", "medium", "low")
MAX_REPRESENTATIVE_CHANGES = 5


def representative_changes(classified_changes: list[dict]) -> list[dict]:
    """Return deterministic representative schema changes for reports."""
    severity_rank = {severity: index for index, severity in enumerate(SEVERITIES)}
    indexed_changes = []

    for index, change in enumerate(classified_changes):
        severity = change["severity"]
        if severity not in severity_rank:
            raise ValueError(f"Unknown severity: {severity}")
        indexed_changes.append((severity_rank[severity], index, change))

    selected_changes = sorted(indexed_changes)[:MAX_REPRESENTATIVE_CHANGES]
    representatives = []

    for _, _, change in selected_changes:
        representative = {
            "severity": change["severity"],
            "change_type": change["change_type"],
            "path": change["path"],
        }

        if change["change_type"] == "type_changed":
            previous = change.get("previous")
            current = change.get("current")
            if isinstance(previous, list) and isinstance(current, list):
                representative["previous_types"] = list(previous)
                representative["current_types"] = list(current)

        representatives.append(representative)

    return representatives
