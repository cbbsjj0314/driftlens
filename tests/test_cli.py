import json
from pathlib import Path

from typer.testing import CliRunner

from driftlens.cli import app
from driftlens.storage.artifacts import read_json_artifact


FIXTURE_DIR = Path(__file__).parent / "fixtures"


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
    assert "# DriftLens Schema Drift Report" in report
    assert read_json_artifact(out_dir / "summary.json") == summary


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


def test_detect_command_fails_for_non_object_json_root(tmp_path) -> None:
    runner = CliRunner()
    previous_json = tmp_path / "previous.json"
    current_json = tmp_path / "current.json"
    previous_json.write_text("[1, 2, 3]\n", encoding="utf-8")
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
