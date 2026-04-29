def infer_type(value: object) -> str:
    """Return the DriftLens schema type for a JSON-compatible value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"

    return "unknown"


def _extract_fields(data: dict, parent_path: str = "") -> list[dict]:
    fields = []
    for key, value in data.items():
        path = f"{parent_path}.{key}" if parent_path else key
        inferred_type = infer_type(value)
        fields.append(
            {
                "path": path,
                "types": [inferred_type],
                "nullable": inferred_type == "null",
            }
        )
        if isinstance(value, dict):
            fields.extend(_extract_fields(value, path))
        if isinstance(value, list):
            fields.extend(_extract_array_item_fields(value, path))

    return fields


def _extract_array_item_fields(items: list, array_path: str) -> list[dict]:
    fields = []
    item_path = f"{array_path}[]"

    for item in items:
        inferred_type = infer_type(item)
        fields.append(
            {
                "path": item_path,
                "types": [inferred_type],
                "nullable": inferred_type == "null",
            }
        )
        if isinstance(item, dict):
            fields.extend(_extract_fields(item, item_path))

    return fields


def _merge_fields(fields: list[dict]) -> list[dict]:
    fields_by_path = {}
    for field in fields:
        path = field["path"]
        if path not in fields_by_path:
            fields_by_path[path] = {
                "path": path,
                "types": set(),
                "nullable": False,
            }

        fields_by_path[path]["types"].update(field["types"])
        fields_by_path[path]["nullable"] = (
            fields_by_path[path]["nullable"] or field["nullable"]
        )

    merged_fields = []
    for field in fields_by_path.values():
        merged_fields.append(
            {
                "path": field["path"],
                "types": sorted(field["types"]),
                "nullable": field["nullable"],
            }
        )

    return merged_fields


def extract_schema(data: dict) -> dict:
    """Extract a deterministic schema description from a JSON object."""
    fields = _merge_fields(_extract_fields(data))
    fields.sort(key=lambda field: field["path"])

    return {"fields": fields}
