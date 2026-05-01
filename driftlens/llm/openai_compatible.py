import json

import openai

from driftlens.llm.representative import representative_changes


SEVERITIES = ("high", "medium", "low")


def _severity_counts(classified_changes: list[dict]) -> dict[str, int]:
    counts = {severity: 0 for severity in SEVERITIES}

    for change in classified_changes:
        severity = change["severity"]
        if severity not in counts:
            raise ValueError(f"Unknown severity: {severity}")
        counts[severity] += 1

    return counts


def _overall_severity(severity_counts: dict[str, int]) -> str:
    for severity in SEVERITIES:
        if severity_counts[severity] > 0:
            return severity

    return "none"


def _messages(
    *,
    previous_schema_hash: str,
    current_schema_hash: str,
    classified_changes: list[dict],
) -> list[dict]:
    payload = {
        "previous_schema_hash": previous_schema_hash,
        "current_schema_hash": current_schema_hash,
        "classified_changes": classified_changes,
    }

    return [
        {
            "role": "system",
            "content": (
                "You analyze classified schema drift for a data pipeline operator. "
                "Return only a JSON object. Do not return Markdown fenced code blocks. "
                "Do not perform schema extraction, schema diffing, or severity judgment. "
                "Only write these fields: operator_summary, impacts, "
                "normalization_suggestions, test_case_suggestions."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(payload, sort_keys=True, separators=(",", ":")),
        },
    ]


def _parse_response_content(content: str) -> dict:
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("LLM response content must be a JSON object") from exc

    if not isinstance(parsed, dict):
        raise ValueError("LLM response content must be a JSON object")

    return parsed


def _string_or_empty(value: object) -> str:
    if isinstance(value, str):
        return value

    return ""


def _list_or_empty(value: object) -> list:
    if isinstance(value, list):
        return value

    return []


class OpenAICompatibleLLMProvider:
    """Call an OpenAI-compatible chat completions API for drift analysis."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
        client=None,
    ) -> None:
        self.model = model

        if client is not None:
            self.client = client
            return

        client_kwargs = {"api_key": api_key}
        if base_url is not None:
            client_kwargs["base_url"] = base_url

        self.client = openai.OpenAI(**client_kwargs)

    def analyze_diff(
        self,
        *,
        previous_schema_hash: str,
        current_schema_hash: str,
        classified_changes: list[dict],
    ) -> dict:
        severity_counts = _severity_counts(classified_changes)
        overall_severity = _overall_severity(severity_counts)
        change_count = len(classified_changes)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=_messages(
                previous_schema_hash=previous_schema_hash,
                current_schema_hash=current_schema_hash,
                classified_changes=classified_changes,
            ),
            temperature=0,
        )
        llm_analysis = _parse_response_content(response.choices[0].message.content)

        return {
            "provider": "openai-compatible",
            "previous_schema_hash": previous_schema_hash,
            "current_schema_hash": current_schema_hash,
            "change_count": change_count,
            "severity_counts": severity_counts,
            "overall_severity": overall_severity,
            "operator_summary": _string_or_empty(
                llm_analysis.get("operator_summary")
            ),
            "representative_changes": representative_changes(classified_changes),
            "impacts": _list_or_empty(llm_analysis.get("impacts")),
            "normalization_suggestions": _list_or_empty(
                llm_analysis.get("normalization_suggestions")
            ),
            "test_case_suggestions": _list_or_empty(
                llm_analysis.get("test_case_suggestions")
            ),
        }
