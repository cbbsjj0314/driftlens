import json
from pathlib import Path
from typing import Annotated

import typer

from driftlens.schema.diff import diff_schemas
from driftlens.schema.extractor import extract_schema
from driftlens.schema.hash import schema_hash
from driftlens.schema.severity import classify_changes
from driftlens.storage.artifacts import write_json_artifact


app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    pass


def _load_json_object(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise typer.BadParameter("JSON root must be an object")

    return data


def _severity_counts(classified_changes: list[dict]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for change in classified_changes:
        counts[change["severity"]] += 1

    return counts


@app.command()
def detect(
    previous_json: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True),
    ],
    current_json: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True),
    ],
    out_dir: Annotated[Path, typer.Option("--out-dir")],
) -> None:
    previous_data = _load_json_object(previous_json)
    current_data = _load_json_object(current_json)

    previous_schema = extract_schema(previous_data)
    current_schema = extract_schema(current_data)
    changes = diff_schemas(previous_schema, current_schema)
    classified_changes = classify_changes(changes)

    artifact_paths = {
        "previous_sample": "samples/previous.json",
        "current_sample": "samples/current.json",
        "previous_schema": "schemas/previous.json",
        "current_schema": "schemas/current.json",
        "schema_diff": "diffs/schema_diff.json",
        "classified_diff": "diffs/classified_diff.json",
        "summary": "summary.json",
    }

    summary = {
        "previous_schema_hash": schema_hash(previous_schema),
        "current_schema_hash": schema_hash(current_schema),
        "change_count": len(classified_changes),
        "severity_counts": _severity_counts(classified_changes),
        "artifacts": artifact_paths,
    }

    write_json_artifact(out_dir, artifact_paths["previous_sample"], previous_data)
    write_json_artifact(out_dir, artifact_paths["current_sample"], current_data)
    write_json_artifact(out_dir, artifact_paths["previous_schema"], previous_schema)
    write_json_artifact(out_dir, artifact_paths["current_schema"], current_schema)
    write_json_artifact(out_dir, artifact_paths["schema_diff"], changes)
    write_json_artifact(out_dir, artifact_paths["classified_diff"], classified_changes)
    write_json_artifact(out_dir, artifact_paths["summary"], summary)

    typer.echo(json.dumps(summary, sort_keys=True))
