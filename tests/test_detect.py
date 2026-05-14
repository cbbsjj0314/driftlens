from copy import deepcopy
from pathlib import Path

from driftlens.detect import run_detection
from driftlens.storage.artifacts import read_json_artifact


FIXTURE_DIR = Path(__file__).parent / "fixtures"
SANITIZED_STEAM_APPDETAILS_DIR = (
    Path(__file__).parents[1] / "examples" / "sanitized-steam-appdetails"
)


class FakeAnalysisProvider:
    def analyze_diff(
        self,
        *,
        previous_schema_hash: str,
        current_schema_hash: str,
        classified_changes: list[dict],
    ) -> dict:
        return {
            "provider": "fake",
            "previous_schema_hash": previous_schema_hash,
            "current_schema_hash": current_schema_hash,
            "change_count": len(classified_changes),
            "severity_counts": {"high": 0, "medium": 0, "low": 0},
            "overall_severity": "none",
            "operator_summary": "Fake analysis.",
            "representative_changes": [],
            "impacts": [],
            "normalization_suggestions": [],
            "test_case_suggestions": [],
        }


def _fixture(name: str) -> dict:
    return read_json_artifact(FIXTURE_DIR / name)


def _sanitized_steam_appdetails_fixture(name: str) -> dict:
    return read_json_artifact(SANITIZED_STEAM_APPDETAILS_DIR / name)


def test_run_detection_writes_default_artifacts_and_summary(tmp_path) -> None:
    previous_data = _fixture("steam_appdetails_v1.json")
    current_data = _fixture("steam_appdetails_nested_v1.json")
    original_previous_data = deepcopy(previous_data)
    original_current_data = deepcopy(current_data)
    out_dir = tmp_path / "artifacts"

    summary = run_detection(previous_data, current_data, out_dir)

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

    for relative_path in expected_artifacts.values():
        assert (out_dir / relative_path).exists()

    assert read_json_artifact(out_dir / "summary.json") == summary
    assert previous_data == original_previous_data
    assert current_data == original_current_data


def test_run_detection_with_provider_writes_analysis_and_markdown_report(
    tmp_path,
) -> None:
    previous_data = _fixture("steam_appdetails_v1.json")
    current_data = _fixture("steam_appdetails_nested_v1.json")
    out_dir = tmp_path / "artifacts"

    summary = run_detection(
        previous_data,
        current_data,
        out_dir,
        FakeAnalysisProvider(),
    )

    assert summary["artifacts"]["llm_analysis"] == "llm/analysis.json"
    assert summary["artifacts"]["markdown_report"] == "reports/schema_drift.md"
    assert (out_dir / "llm/analysis.json").exists()
    assert (out_dir / "reports/schema_drift.md").exists()

    analysis = read_json_artifact(out_dir / "llm/analysis.json")
    markdown_report = (out_dir / "reports/schema_drift.md").read_text(
        encoding="utf-8"
    )

    assert analysis["provider"] == "fake"
    assert "# DriftLens Schema Drift Report" in markdown_report
    assert read_json_artifact(out_dir / "summary.json") == summary


def test_run_detection_with_sanitized_steam_appdetails_demo_fixtures(
    tmp_path,
) -> None:
    previous_data = _sanitized_steam_appdetails_fixture("previous.json")
    current_data = _sanitized_steam_appdetails_fixture("current.json")
    out_dir = tmp_path / "artifacts"

    summary = run_detection(previous_data, current_data, out_dir)

    assert (out_dir / "summary.json").exists()
    assert (out_dir / "diffs/classified_diff.json").exists()
    assert read_json_artifact(out_dir / "summary.json") == summary

    classified_diff = read_json_artifact(out_dir / "diffs/classified_diff.json")
    changes_by_path = {change["path"]: change for change in classified_diff}

    assert {
        "required_age",
        "price_overview",
        "price_overview.currency",
        "ratings.agcom.rating",
    } <= changes_by_path.keys()
    assert changes_by_path["required_age"]["change_type"] == "type_changed"
    assert changes_by_path["price_overview"]["change_type"] == "field_removed"
    assert (
        changes_by_path["price_overview.currency"]["change_type"]
        == "field_removed"
    )
    assert changes_by_path["ratings.agcom.rating"]["change_type"] == "field_added"

    assert {
        "field_removed",
        "field_added",
        "type_changed",
    } <= {change["change_type"] for change in classified_diff}
