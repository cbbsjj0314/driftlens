SEVERITIES = ("high", "medium", "low")


def _format_bullets(items: list, fallback: str) -> list[str]:
    if not items:
        return [f"- {fallback}"]

    return [f"- {item}" for item in items]


def _operator_summary(summary: str) -> str:
    if summary:
        return summary

    return "No operator summary provided."


def _format_representative_change(change: dict) -> str:
    summary = f"{change['severity']} {change['change_type']}: {change['path']}"

    previous_types = change.get("previous_types")
    current_types = change.get("current_types")
    if isinstance(previous_types, list) and isinstance(current_types, list):
        previous = ", ".join(str(value) for value in previous_types)
        current = ", ".join(str(value) for value in current_types)
        summary = f"{summary} ({previous} -> {current})"

    return f"- {summary}"


def _format_representative_changes(changes: list) -> list[str]:
    if not changes:
        return ["- No representative changes provided."]

    return [_format_representative_change(change) for change in changes]


def render_markdown_report(analysis: dict) -> str:
    """Render an operator-facing Markdown report from an LLM analysis dict."""
    severity_counts = analysis["severity_counts"]

    lines = [
        "# DriftLens Schema Drift Report",
        "",
        "## Summary",
        "",
        f"- Provider: {analysis['provider']}",
        f"- Change count: {analysis['change_count']}",
        f"- Overall severity: {analysis['overall_severity']}",
        f"- Operator summary: {_operator_summary(analysis['operator_summary'])}",
        "",
        "## Schema Versions",
        "",
        f"- Previous schema hash: {analysis['previous_schema_hash']}",
        f"- Current schema hash: {analysis['current_schema_hash']}",
        "",
        "## Severity",
        "",
    ]

    for severity in SEVERITIES:
        lines.append(f"- {severity}: {severity_counts[severity]}")

    lines.extend(
        [
            "",
            "## Representative Changes",
            "",
            *_format_representative_changes(analysis.get("representative_changes")),
            "",
            "## Impacts",
            "",
            *_format_bullets(analysis["impacts"], "No impacts provided."),
            "",
            "## Normalization Suggestions",
            "",
            *_format_bullets(
                analysis["normalization_suggestions"],
                "No normalization suggestions provided.",
            ),
            "",
            "## Test Case Suggestions",
            "",
            *_format_bullets(
                analysis["test_case_suggestions"],
                "No test case suggestions provided.",
            ),
            "",
        ]
    )

    return "\n".join(lines)
