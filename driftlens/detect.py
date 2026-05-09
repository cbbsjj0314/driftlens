from copy import deepcopy
from pathlib import Path
from typing import Protocol

from driftlens.reports.markdown import render_markdown_report
from driftlens.schema.diff import diff_schemas
from driftlens.schema.extractor import extract_schema
from driftlens.schema.hash import schema_hash
from driftlens.schema.severity import classify_changes
from driftlens.schema.severity_summary import severity_counts
from driftlens.storage.artifacts import write_json_artifact, write_text_artifact


class AnalysisProviderProtocol(Protocol):
    def analyze_diff(
        self,
        *,
        previous_schema_hash: str,
        current_schema_hash: str,
        classified_changes: list[dict],
    ) -> dict:
        pass


def run_detection(
    previous_data: dict,
    current_data: dict,
    out_dir: Path,
    analysis_provider: AnalysisProviderProtocol | None = None,
) -> dict:
    previous_sample = deepcopy(previous_data)
    current_sample = deepcopy(current_data)

    previous_schema = extract_schema(previous_sample)
    current_schema = extract_schema(current_sample)
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

    if analysis_provider is not None:
        artifact_paths["llm_analysis"] = "llm/analysis.json"
        artifact_paths["markdown_report"] = "reports/schema_drift.md"

    summary = {
        "previous_schema_hash": previous_schema_hash,
        "current_schema_hash": current_schema_hash,
        "change_count": len(classified_changes),
        "severity_counts": severity_counts(classified_changes),
        "artifacts": artifact_paths,
    }

    write_json_artifact(out_dir, artifact_paths["previous_sample"], previous_sample)
    write_json_artifact(out_dir, artifact_paths["current_sample"], current_sample)
    write_json_artifact(out_dir, artifact_paths["previous_schema"], previous_schema)
    write_json_artifact(out_dir, artifact_paths["current_schema"], current_schema)
    write_json_artifact(out_dir, artifact_paths["schema_diff"], changes)
    write_json_artifact(out_dir, artifact_paths["classified_diff"], classified_changes)

    if analysis_provider is not None:
        analysis = analysis_provider.analyze_diff(
            previous_schema_hash=previous_schema_hash,
            current_schema_hash=current_schema_hash,
            classified_changes=classified_changes,
        )
        markdown_report = render_markdown_report(analysis)
        write_json_artifact(out_dir, artifact_paths["llm_analysis"], analysis)
        write_text_artifact(out_dir, artifact_paths["markdown_report"], markdown_report)

    write_json_artifact(out_dir, artifact_paths["summary"], summary)

    return summary
