import hashlib
import json

from driftlens.schema.types import ObservedSchema


def _canonicalize_schema(schema: ObservedSchema) -> ObservedSchema:
    fields = [
        {
            "path": field["path"],
            "types": sorted(field["types"]),
            "nullable": field["nullable"],
        }
        for field in schema["fields"]
    ]
    fields.sort(key=lambda field: field["path"])

    return {"fields": fields}


def schema_hash(schema: ObservedSchema) -> str:
    """Return a stable SHA-256 hash for an observed schema."""
    canonical_schema = _canonicalize_schema(schema)
    canonical_json = json.dumps(
        canonical_schema,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
