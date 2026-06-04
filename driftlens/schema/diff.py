from driftlens.schema.types import (
    ObservedSchema,
    SchemaChange,
    SchemaField,
    SchemaValueType,
)


def _fields_by_path(schema: ObservedSchema) -> dict[str, SchemaField]:
    return {field["path"]: field for field in schema["fields"]}


def _value_types(field: SchemaField) -> list[SchemaValueType]:
    return [field_type for field_type in field["types"] if field_type != "null"]


def diff_schemas(
    previous: ObservedSchema, current: ObservedSchema
) -> list[SchemaChange]:
    """Return deterministic schema changes between two observed schemas."""
    previous_fields = _fields_by_path(previous)
    current_fields = _fields_by_path(current)
    changes: list[SchemaChange] = []

    for path in previous_fields.keys() - current_fields.keys():
        changes.append(
            {
                "change_type": "field_removed",
                "path": path,
                "previous": previous_fields[path],
                "current": None,
            }
        )

    for path in current_fields.keys() - previous_fields.keys():
        changes.append(
            {
                "change_type": "field_added",
                "path": path,
                "previous": None,
                "current": current_fields[path],
            }
        )

    for path in previous_fields.keys() & current_fields.keys():
        previous_field = previous_fields[path]
        current_field = current_fields[path]

        previous_types = _value_types(previous_field)
        current_types = _value_types(current_field)

        if previous_types != current_types:
            changes.append(
                {
                    "change_type": "type_changed",
                    "path": path,
                    "previous": previous_types,
                    "current": current_types,
                }
            )

        if previous_field["nullable"] != current_field["nullable"]:
            changes.append(
                {
                    "change_type": "nullability_changed",
                    "path": path,
                    "previous": previous_field["nullable"],
                    "current": current_field["nullable"],
                }
            )

    changes.sort(key=lambda change: (change["path"], change["change_type"]))
    return changes
