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

    return fields


def extract_schema(data: dict) -> dict:
    """Extract a deterministic schema description from a JSON object."""
    fields = _extract_fields(data)
    fields.sort(key=lambda field: field["path"])

    return {"fields": fields}
