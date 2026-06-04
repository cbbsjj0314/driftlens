import importlib
import json
import os
from enum import Enum
from pathlib import Path
from typing import Annotated

import click
import typer

from driftlens.detect import run_detection
from driftlens.llm.errors import LLMResponseError
from driftlens.llm.mock import MockLLMProvider


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
    try:
        raw_json = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"Failed to read JSON file '{path}': {exc}") from exc

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException(
            f"Invalid JSON in '{path}' at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        root_type = _json_root_type_name(data)
        raise typer.BadParameter(f"JSON root must be an object; got {root_type}")

    return data


def _get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        raise click.ClickException(f"{name} is required for openai-compatible analysis")

    return value


def _optional_env(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None or value == "":
        return None

    return value


def _load_openai_compatible_provider_class():
    try:
        module = importlib.import_module("driftlens.llm.openai_compatible")
    except ModuleNotFoundError as exc:
        if exc.name == "openai":
            raise click.ClickException(
                "openai-compatible analysis requires the llm extra. "
                "Install with `uv sync --extra llm`."
            ) from exc
        raise

    return module.OpenAICompatibleLLMProvider


def _build_analysis_provider(provider: AnalysisProvider):
    if provider == AnalysisProvider.mock:
        return MockLLMProvider()

    openai_compatible_provider_class = _load_openai_compatible_provider_class()
    return openai_compatible_provider_class(
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

    if report:
        provider = _build_analysis_provider(analysis_provider)
        try:
            summary = run_detection(previous_data, current_data, out_dir, provider)
        except LLMResponseError as exc:
            if analysis_provider != AnalysisProvider.openai_compatible:
                raise
            raise click.ClickException(
                f"OpenAI-compatible analysis failed: {exc}"
            ) from exc
    else:
        summary = run_detection(previous_data, current_data, out_dir)

    typer.echo(json.dumps(summary, sort_keys=True))
