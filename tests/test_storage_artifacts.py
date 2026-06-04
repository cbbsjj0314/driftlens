import pytest

from driftlens.schema.diff import diff_schemas
from driftlens.schema.extractor import extract_schema
from driftlens.schema.severity import classify_changes
from driftlens.storage.artifacts import (
    read_json_artifact,
    write_json_artifact,
    write_text_artifact,
)


def test_write_json_artifact_can_be_read_back(tmp_path) -> None:
    data = {"name": "Example Game", "appid": 123}

    artifact_path = write_json_artifact(tmp_path, "samples/raw.json", data)

    assert read_json_artifact(artifact_path) == data


def test_write_json_artifact_creates_parent_directories(tmp_path) -> None:
    artifact_path = write_json_artifact(
        tmp_path,
        "schemas/steam/appdetails.json",
        {"fields": []},
    )

    assert artifact_path.exists()
    assert artifact_path.parent == tmp_path / "schemas" / "steam"


def test_write_json_artifact_uses_deterministic_json_formatting(tmp_path) -> None:
    data = {"name": "예제 게임", "appid": 123}

    artifact_path = write_json_artifact(tmp_path, "samples/raw.json", data)

    assert artifact_path.read_text(encoding="utf-8") == (
        '{\n  "appid": 123,\n  "name": "예제 게임"\n}\n'
    )


def test_write_json_artifact_rejects_relative_path_traversal(tmp_path) -> None:
    with pytest.raises(ValueError):
        write_json_artifact(tmp_path, "../outside.json", {"ok": True})


def test_write_json_artifact_rejects_absolute_path(tmp_path) -> None:
    with pytest.raises(ValueError):
        write_json_artifact(tmp_path, str(tmp_path / "outside.json"), {"ok": True})


def test_write_json_artifact_allows_dotdot_in_filename_part(tmp_path) -> None:
    artifact_path = write_json_artifact(tmp_path, "samples/raw..json", {"ok": True})

    assert read_json_artifact(artifact_path) == {"ok": True}


def test_write_text_artifact_writes_utf8_text_with_trailing_newline(tmp_path) -> None:
    artifact_path = write_text_artifact(
        tmp_path,
        "reports/schema_drift.md",
        "# 리포트",
    )

    assert artifact_path.read_text(encoding="utf-8") == "# 리포트\n"


def test_write_text_artifact_does_not_duplicate_trailing_newline(tmp_path) -> None:
    artifact_path = write_text_artifact(
        tmp_path,
        "reports/schema_drift.md",
        "# Report\n",
    )

    assert artifact_path.read_text(encoding="utf-8") == "# Report\n"


def test_write_text_artifact_rejects_relative_path_traversal(tmp_path) -> None:
    with pytest.raises(ValueError):
        write_text_artifact(tmp_path, "../outside.md", "# Report")


def test_write_text_artifact_rejects_absolute_path(tmp_path) -> None:
    with pytest.raises(ValueError):
        write_text_artifact(tmp_path, str(tmp_path / "outside.md"), "# Report")


def test_write_json_artifact_stores_observed_schema_dict(tmp_path) -> None:
    observed_schema = extract_schema(
        {
            "appid": 123,
            "name": "Example Game",
            "price": {"currency": "KRW", "final": 12000},
        }
    )

    artifact_path = write_json_artifact(
        tmp_path,
        "schemas/steam_appdetails.json",
        observed_schema,
    )

    assert read_json_artifact(artifact_path) == observed_schema


def test_write_json_artifact_stores_diff_and_classified_diff_lists(tmp_path) -> None:
    previous_schema = extract_schema(
        {
            "appid": 123,
            "name": "Example Game",
            "price": 12000,
            "currency": "KRW",
        }
    )
    current_schema = extract_schema(
        {
            "appid": 123,
            "name": "Example Game",
            "price": {"currency": "KRW", "final": 12000},
        }
    )
    changes = diff_schemas(previous_schema, current_schema)
    classified_changes = classify_changes(changes)

    diff_path = write_json_artifact(tmp_path, "diffs/appdetails.json", changes)
    classified_path = write_json_artifact(
        tmp_path,
        "diffs/appdetails_classified.json",
        classified_changes,
    )

    assert read_json_artifact(diff_path) == changes
    assert read_json_artifact(classified_path) == classified_changes
