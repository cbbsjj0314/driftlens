import json

import openai

from driftlens.llm.errors import LLMResponseError
from driftlens.llm.representative import representative_changes
from driftlens.schema.severity_summary import overall_severity, severity_counts


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
                "Return only a JSON object, with no surrounding prose. "
                "Do not return Markdown fenced code blocks. "
                "Do not perform schema extraction, schema diffing, or severity judgment; "
                "those deterministic judgments are already complete. "
                "Base your analysis only on classified_changes. "
                "Only write these allowed fields: operator_summary, impacts, "
                "normalization_suggestions, test_case_suggestions. "
                "Do not write or overwrite deterministic fields such as provider, "
                "previous_schema_hash, current_schema_hash, change_count, "
                "severity_counts, overall_severity, or representative_changes. "
                "operator_summary must be short and operator-facing. "
                "If classified_changes contains drift, impacts, normalization_suggestions, "
                "and test_case_suggestions must each contain at least 1 item, preferably "
                "2 to 5 concrete items. Empty arrays are allowed only when there is no drift. "
                "Each impact should describe a concrete pipeline operation risk. "
                "Each normalization_suggestion should be a concrete parser, normalization, "
                "or table mapping check. "
                "Each test_case_suggestion should be a concrete fixture or regression test "
                "candidate. "
                "Include the affected path from classified_changes whenever possible. "
                "Avoid generic fallback wording; make every item specific to the supplied "
                "change_type, severity, and path."
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
        raise LLMResponseError(
            "LLM response content must be a JSON object"
        ) from exc

    if not isinstance(parsed, dict):
        raise LLMResponseError("LLM response content must be a JSON object")

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
        counts = severity_counts(classified_changes)
        highest_severity = overall_severity(counts)
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
            "severity_counts": counts,
            "overall_severity": highest_severity,
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
