from driftlens.llm.types import RepresentativeChange
from driftlens.schema.severity_summary import severity_rank
from driftlens.schema.types import ClassifiedSchemaChange


MAX_REPRESENTATIVE_CHANGES = 5


def representative_changes(
    classified_changes: list[ClassifiedSchemaChange],
) -> list[RepresentativeChange]:
    """Return deterministic representative schema changes for reports."""
    ranks = severity_rank()
    indexed_changes = []

    for index, change in enumerate(classified_changes):
        severity = change["severity"]
        if severity not in ranks:
            raise ValueError(f"Unknown severity: {severity}")
        indexed_changes.append((ranks[severity], index, change))

    selected_changes = sorted(indexed_changes)[:MAX_REPRESENTATIVE_CHANGES]
    representatives: list[RepresentativeChange] = []

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
