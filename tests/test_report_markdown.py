import copy

from driftlens.llm.mock import MockLLMProvider
from driftlens.reports.markdown import render_markdown_report


def analysis(**overrides) -> dict:
    data = {
        "provider": "test-provider",
        "previous_schema_hash": "previous-hash",
        "current_schema_hash": "current-hash",
        "change_count": 3,
        "severity_counts": {"low": 1, "high": 1, "medium": 1},
        "overall_severity": "high",
        "operator_summary": "Review parser behavior for schema drift.",
        "impacts": [
            "Parser assumptions may need review.",
            "Downstream mapping may need review.",
        ],
        "normalization_suggestions": [
            "Update normalization mapping.",
            "Check nullable field handling.",
        ],
        "test_case_suggestions": [
            "Add a previous/current fixture test.",
            "Add parser regression coverage.",
        ],
    }
    data.update(overrides)

    return data


def test_render_markdown_report_returns_string() -> None:
    report = render_markdown_report(analysis())

    assert isinstance(report, str)


def test_render_markdown_report_includes_title_and_sections_in_order() -> None:
    report = render_markdown_report(analysis())

    headings = [
        "# DriftLens Schema Drift Report",
        "## Summary",
        "## Schema Versions",
        "## Severity",
        "## Impacts",
        "## Normalization Suggestions",
        "## Test Case Suggestions",
    ]

    positions = [report.index(heading) for heading in headings]
    assert positions == sorted(positions)


def test_render_markdown_report_includes_core_scalar_fields() -> None:
    report = render_markdown_report(analysis())

    assert "- Provider: test-provider" in report
    assert "- Previous schema hash: previous-hash" in report
    assert "- Current schema hash: current-hash" in report
    assert "- Change count: 3" in report
    assert "- Overall severity: high" in report


def test_render_markdown_report_renders_severity_counts_in_fixed_order() -> None:
    report = render_markdown_report(
        analysis(severity_counts={"low": 7, "medium": 5, "high": 3})
    )

    assert report.index("- high: 3") < report.index("- medium: 5")
    assert report.index("- medium: 5") < report.index("- low: 7")


def test_render_markdown_report_includes_operator_summary() -> None:
    report = render_markdown_report(
        analysis(operator_summary="Pipeline operator should review parser mappings.")
    )

    assert "Pipeline operator should review parser mappings." in report


def test_render_markdown_report_renders_list_fields_as_bullets_in_input_order() -> None:
    report = render_markdown_report(
        analysis(
            impacts=["Second impact stays second.", "First input order stays first."],
            normalization_suggestions=[
                "Normalize amount.",
                "Normalize currency.",
            ],
            test_case_suggestions=[
                "Add fixture test.",
                "Add parser test.",
            ],
        )
    )

    assert "- Second impact stays second." in report
    assert "- First input order stays first." in report
    assert report.index("- Second impact stays second.") < report.index(
        "- First input order stays first."
    )
    assert "- Normalize amount." in report
    assert "- Normalize currency." in report
    assert "- Add fixture test." in report
    assert "- Add parser test." in report


def test_render_markdown_report_uses_fallbacks_for_empty_summary_and_lists() -> None:
    report = render_markdown_report(
        analysis(
            operator_summary="",
            impacts=[],
            normalization_suggestions=[],
            test_case_suggestions=[],
        )
    )

    assert "No operator summary provided." in report
    assert "- No impacts provided." in report
    assert "- No normalization suggestions provided." in report
    assert "- No test case suggestions provided." in report


def test_render_markdown_report_is_deterministic_for_same_input() -> None:
    input_analysis = analysis()

    assert render_markdown_report(input_analysis) == render_markdown_report(
        input_analysis
    )


def test_render_markdown_report_does_not_mutate_input_analysis() -> None:
    input_analysis = analysis()
    original_analysis = copy.deepcopy(input_analysis)

    render_markdown_report(input_analysis)

    assert input_analysis == original_analysis


def test_render_markdown_report_accepts_mock_llm_provider_output() -> None:
    mock_analysis = MockLLMProvider().analyze_diff(
        previous_schema_hash="previous-hash",
        current_schema_hash="current-hash",
        classified_changes=[
            {
                "change_type": "field_added",
                "severity": "low",
            }
        ],
    )

    report = render_markdown_report(mock_analysis)

    assert "# DriftLens Schema Drift Report" in report
    assert "- Provider: mock" in report
    assert "- low: 1" in report


def test_render_markdown_report_accepts_openai_compatible_analysis_shape() -> None:
    openai_compatible_analysis = analysis(
        provider="openai-compatible",
        operator_summary="Review normalization before release.",
        impacts=["Parser assumptions may need review."],
        normalization_suggestions=["Update mapping."],
        test_case_suggestions=["Add fixture regression coverage."],
    )

    report = render_markdown_report(openai_compatible_analysis)

    assert "- Provider: openai-compatible" in report
    assert "Review normalization before release." in report
