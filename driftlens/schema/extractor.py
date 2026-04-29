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


def extract_schema(data: dict) -> dict:
    """Extract a deterministic schema description from a flat JSON object."""
    fields = []
    for key, value in data.items():
        inferred_type = infer_type(value)
        fields.append(
            {
                "path": key,
                "types": [inferred_type],
                "nullable": inferred_type == "null",
            }
        )

    return {"fields": fields}
