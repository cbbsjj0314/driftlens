import json
import os
from enum import Enum
from pathlib import Path
from typing import Annotated

import click
import typer

from driftlens.llm.errors import LLMResponseError
from driftlens.llm.mock import MockLLMProvider
from driftlens.llm.openai_compatible import OpenAICompatibleLLMProvider
from driftlens.reports.markdown import render_markdown_report
from driftlens.schema.diff import diff_schemas
from driftlens.schema.extractor import extract_schema
from driftlens.schema.hash import schema_hash
from driftlens.schema.severity import classify_changes
from driftlens.storage.artifacts import write_json_artifact, write_text_artifact


app = typer.Typer(no_args_is_help=True)


class AnalysisProvider(str, Enum):
    mock = "mock"
    openai_compatible = "openai-compatible"


@app.callback()
def main() -> None:
    pass


def _json_root_type_name(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int | float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"

    return "object"


def _load_json_object(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        root_type = _json_root_type_name(data)
        raise typer.BadParameter(f"JSON root must be an object; got {root_type}")

    return data


def _severity_counts(classified_changes: list[dict]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for change in classified_changes:
        counts[change["severity"]] += 1

    return counts


def _get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        raise click.ClickException(
            f"{name} is required for openai-compatible analysis"
        )

    return value


def _optional_env(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None or value == "":
        return None

    return value


def _build_analysis_provider(provider: AnalysisProvider):
    if provider == AnalysisProvider.mock:
        return MockLLMProvider()

    return OpenAICompatibleLLMProvider(
        api_key=_get_required_env("LLM_API_KEY"),
        model=_get_required_env("LLM_MODEL"),
        base_url=_optional_env("LLM_BASE_URL"),
    )


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
    report: Annotated[bool, typer.Option("--report")] = False,
    analysis_provider: Annotated[
        AnalysisProvider,
        typer.Option("--analysis-provider"),
    ] = AnalysisProvider.mock,
) -> None:
    if not report and analysis_provider != AnalysisProvider.mock:
        raise click.ClickException("--analysis-provider requires --report")

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

    previous_schema_hash = schema_hash(previous_schema)
    current_schema_hash = schema_hash(current_schema)

    if report:
        artifact_paths["llm_analysis"] = "llm/analysis.json"
        artifact_paths["markdown_report"] = "reports/schema_drift.md"

    summary = {
        "previous_schema_hash": previous_schema_hash,
        "current_schema_hash": current_schema_hash,
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

    if report:
        provider = _build_analysis_provider(analysis_provider)
        try:
            analysis = provider.analyze_diff(
                previous_schema_hash=previous_schema_hash,
                current_schema_hash=current_schema_hash,
                classified_changes=classified_changes,
            )
        except LLMResponseError as exc:
            if analysis_provider != AnalysisProvider.openai_compatible:
                raise
            raise click.ClickException(
                f"OpenAI-compatible analysis failed: {exc}"
            ) from exc
        markdown_report = render_markdown_report(analysis)
        write_json_artifact(out_dir, artifact_paths["llm_analysis"], analysis)
        write_text_artifact(out_dir, artifact_paths["markdown_report"], markdown_report)

    write_json_artifact(out_dir, artifact_paths["summary"], summary)

    typer.echo(json.dumps(summary, sort_keys=True))
