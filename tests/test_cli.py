import json
from pathlib import Path

import driftlens.cli as cli
import pytest
from typer.testing import CliRunner

from driftlens.cli import app
from driftlens.llm.errors import LLMResponseError
from driftlens.storage.artifacts import read_json_artifact


FIXTURE_DIR = Path(__file__).parent / "fixtures"


class FakeOpenAICompatibleLLMProvider:
    calls = []

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.calls.append(
            {
                "api_key": api_key,
                "model": model,
                "base_url": base_url,
            }
        )

    def analyze_diff(
        self,
        *,
        previous_schema_hash: str,
        current_schema_hash: str,
        classified_changes: list[dict],
    ) -> dict:
        return {
            "provider": "openai-compatible",
            "previous_schema_hash": previous_schema_hash,
            "current_schema_hash": current_schema_hash,
            "change_count": len(classified_changes),
            "severity_counts": {"high": 0, "medium": 0, "low": 0},
            "overall_severity": "none",
            "operator_summary": "Fake OpenAI-compatible analysis.",
            "representative_changes": [
                {
                    "severity": "high",
                    "change_type": "type_changed",
                    "path": "price_overview",
                }
            ],
            "impacts": ["Fake impact."],
            "normalization_suggestions": ["Fake normalization suggestion."],
            "test_case_suggestions": ["Fake test suggestion."],
        }


class FakeFailingOpenAICompatibleLLMProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def analyze_diff(
        self,
        *,
        previous_schema_hash: str,
        current_schema_hash: str,
        classified_changes: list[dict],
    ) -> dict:
        raise LLMResponseError("LLM response content must be a JSON object")


class FakeFailingMockLLMProvider:
    def analyze_diff(
        self,
        *,
        previous_schema_hash: str,
        current_schema_hash: str,
        classified_changes: list[dict],
    ) -> dict:
        raise LLMResponseError("Mock analysis failed")


def test_detect_command_writes_artifacts_and_prints_json_summary(tmp_path) -> None:
    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"
    out_dir = tmp_path / "artifacts"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0
    summary = json.loads(result.stdout)

    assert set(summary) == {
        "previous_schema_hash",
        "current_schema_hash",
        "change_count",
        "severity_counts",
        "artifacts",
    }
    assert set(summary["severity_counts"]) == {"high", "medium", "low"}

    expected_artifacts = {
        "previous_sample": "samples/previous.json",
        "current_sample": "samples/current.json",
        "previous_schema": "schemas/previous.json",
        "current_schema": "schemas/current.json",
        "schema_diff": "diffs/schema_diff.json",
        "classified_diff": "diffs/classified_diff.json",
        "summary": "summary.json",
    }
    assert summary["artifacts"] == expected_artifacts
    assert all(not Path(path).is_absolute() for path in summary["artifacts"].values())

    for relative_path in expected_artifacts.values():
        assert (out_dir / relative_path).exists()

    schema_diff = read_json_artifact(out_dir / "diffs/schema_diff.json")
    classified_diff = read_json_artifact(out_dir / "diffs/classified_diff.json")

    assert schema_diff
    assert classified_diff
    assert summary["change_count"] == len(classified_diff)
    assert all("severity" in change for change in classified_diff)
    assert read_json_artifact(out_dir / "summary.json") == summary


def test_detect_command_with_report_defaults_to_mock_analysis_provider(
    tmp_path,
) -> None:
    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"
    out_dir = tmp_path / "artifacts"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(out_dir),
            "--report",
        ],
    )

    assert result.exit_code == 0

    analysis = read_json_artifact(out_dir / "llm/analysis.json")

    assert analysis["provider"] == "mock"


def test_detect_command_with_report_writes_mock_analysis_and_markdown_report(
    tmp_path,
) -> None:
    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"
    out_dir = tmp_path / "artifacts"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(out_dir),
            "--report",
        ],
    )

    assert result.exit_code == 0
    summary = json.loads(result.stdout)

    assert summary["artifacts"]["llm_analysis"] == "llm/analysis.json"
    assert summary["artifacts"]["markdown_report"] == "reports/schema_drift.md"

    analysis = read_json_artifact(out_dir / "llm/analysis.json")
    report = (out_dir / "reports/schema_drift.md").read_text(encoding="utf-8")

    assert analysis["provider"] == "mock"
    assert "representative_changes" in analysis
    assert analysis["representative_changes"]
    assert "# DriftLens Schema Drift Report" in report
    assert "## Representative Changes" in report
    assert read_json_artifact(out_dir / "summary.json") == summary


def test_detect_command_with_explicit_mock_analysis_provider_writes_mock_report(
    tmp_path,
) -> None:
    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"
    out_dir = tmp_path / "artifacts"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(out_dir),
            "--report",
            "--analysis-provider",
            "mock",
        ],
    )

    assert result.exit_code == 0

    analysis = read_json_artifact(out_dir / "llm/analysis.json")
    report = (out_dir / "reports/schema_drift.md").read_text(encoding="utf-8")

    assert analysis["provider"] == "mock"
    assert "## Representative Changes" in report


def test_detect_command_with_openai_compatible_analysis_provider_uses_env(
    tmp_path,
    monkeypatch,
) -> None:
    FakeOpenAICompatibleLLMProvider.calls = []
    monkeypatch.setattr(
        cli,
        "OpenAICompatibleLLMProvider",
        FakeOpenAICompatibleLLMProvider,
    )
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.example.test/v1")

    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"
    out_dir = tmp_path / "artifacts"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(out_dir),
            "--report",
            "--analysis-provider",
            "openai-compatible",
        ],
    )

    assert result.exit_code == 0
    summary = json.loads(result.stdout)

    assert FakeOpenAICompatibleLLMProvider.calls == [
        {
            "api_key": "test-api-key",
            "model": "test-model",
            "base_url": "https://api.example.test/v1",
        }
    ]
    assert summary["artifacts"]["llm_analysis"] == "llm/analysis.json"
    assert summary["artifacts"]["markdown_report"] == "reports/schema_drift.md"

    analysis = read_json_artifact(out_dir / "llm/analysis.json")
    report = (out_dir / "reports/schema_drift.md").read_text(encoding="utf-8")

    assert analysis["provider"] == "openai-compatible"
    assert "- Provider: openai-compatible" in report
    assert "## Representative Changes" in report
    assert read_json_artifact(out_dir / "summary.json") == summary


def test_detect_command_with_openai_compatible_treats_unset_base_url_as_none(
    tmp_path,
    monkeypatch,
) -> None:
    FakeOpenAICompatibleLLMProvider.calls = []
    monkeypatch.setattr(
        cli,
        "OpenAICompatibleLLMProvider",
        FakeOpenAICompatibleLLMProvider,
    )
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)

    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(tmp_path / "artifacts"),
            "--report",
            "--analysis-provider",
            "openai-compatible",
        ],
    )

    assert result.exit_code == 0
    assert FakeOpenAICompatibleLLMProvider.calls[0]["base_url"] is None


def test_detect_command_with_openai_compatible_treats_empty_base_url_as_none(
    tmp_path,
    monkeypatch,
) -> None:
    FakeOpenAICompatibleLLMProvider.calls = []
    monkeypatch.setattr(
        cli,
        "OpenAICompatibleLLMProvider",
        FakeOpenAICompatibleLLMProvider,
    )
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_BASE_URL", "")

    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(tmp_path / "artifacts"),
            "--report",
            "--analysis-provider",
            "openai-compatible",
        ],
    )

    assert result.exit_code == 0
    assert FakeOpenAICompatibleLLMProvider.calls[0]["base_url"] is None


def test_detect_command_with_openai_compatible_fails_without_required_env(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_MODEL", "test-model")

    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(tmp_path / "artifacts"),
            "--report",
            "--analysis-provider",
            "openai-compatible",
        ],
    )

    assert result.exit_code != 0
    assert "LLM_API_KEY is required for openai-compatible analysis" in result.output


def test_detect_command_with_openai_compatible_fails_without_model_env(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "")

    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(tmp_path / "artifacts"),
            "--report",
            "--analysis-provider",
            "openai-compatible",
        ],
    )

    assert result.exit_code != 0
    assert "LLM_MODEL is required for openai-compatible analysis" in result.output


def test_detect_command_with_openai_compatible_fails_without_report(
    tmp_path,
) -> None:
    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(tmp_path / "artifacts"),
            "--analysis-provider",
            "openai-compatible",
        ],
    )

    assert result.exit_code != 0
    assert "--analysis-provider requires --report" in result.output


def test_detect_command_with_openai_compatible_surfaces_response_parse_error(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "OpenAICompatibleLLMProvider",
        FakeFailingOpenAICompatibleLLMProvider,
    )
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(tmp_path / "artifacts"),
            "--report",
            "--analysis-provider",
            "openai-compatible",
        ],
        terminal_width=120,
    )

    output_text = result.output.translate(
        str.maketrans("", "", "╭─╮│╰╯")
    )
    normalized_output = " ".join(output_text.split())

    assert result.exit_code != 0
    assert (
        "OpenAI-compatible analysis failed: "
        "LLM response content must be a JSON object"
    ) in normalized_output


def test_detect_command_does_not_wrap_mock_response_error(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(cli, "MockLLMProvider", FakeFailingMockLLMProvider)

    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(tmp_path / "artifacts"),
            "--report",
        ],
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, LLMResponseError)
    assert "OpenAI-compatible analysis failed" not in result.output


def test_detect_command_fails_for_unknown_analysis_provider(tmp_path) -> None:
    runner = CliRunner()
    previous_json = FIXTURE_DIR / "steam_appdetails_v1.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(tmp_path / "artifacts"),
            "--report",
            "--analysis-provider",
            "unknown",
        ],
    )

    assert result.exit_code != 0
    assert "unknown" in result.output


def test_detect_command_fails_for_missing_input_file(tmp_path) -> None:
    runner = CliRunner()
    missing_json = tmp_path / "missing.json"
    current_json = FIXTURE_DIR / "steam_appdetails_nested_v1.json"

    result = runner.invoke(
        app,
        [
            "detect",
            str(missing_json),
            str(current_json),
            "--out-dir",
            str(tmp_path / "artifacts"),
        ],
    )

    assert result.exit_code != 0


@pytest.mark.parametrize(
    ("json_content", "type_name"),
    [
        ("[1, 2, 3]\n", "array"),
        ("null\n", "null"),
        ('"appid"\n', "string"),
        ("123\n", "number"),
        ("true\n", "boolean"),
    ],
)
def test_detect_command_fails_for_non_object_json_root(
    tmp_path,
    json_content,
    type_name,
) -> None:
    runner = CliRunner()
    previous_json = tmp_path / "previous.json"
    current_json = tmp_path / "current.json"
    previous_json.write_text(json_content, encoding="utf-8")
    current_json.write_text('{"appid": 123}\n', encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "detect",
            str(previous_json),
            str(current_json),
            "--out-dir",
            str(tmp_path / "artifacts"),
        ],
    )

    assert result.exit_code != 0
    assert f"JSON root must be an object; got {type_name}" in result.output
