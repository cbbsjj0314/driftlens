import copy
import json

import pytest

pytest.importorskip("openai")

import driftlens.llm.openai_compatible as openai_compatible
from driftlens.llm.errors import LLMResponseError
from driftlens.llm.openai_compatible import OpenAICompatibleLLMProvider


def field(path: str, types: list[str], nullable: bool = False) -> dict:
    return {"path": path, "types": types, "nullable": nullable}


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = []

    def create(self, **kwargs) -> FakeResponse:
        self.calls.append(kwargs)
        return FakeResponse(self.content)


class FakeChat:
    def __init__(self, content: str) -> None:
        self.completions = FakeCompletions(content)


class FakeClient:
    def __init__(self, content: str) -> None:
        self.chat = FakeChat(content)


def fake_llm_content(**overrides) -> str:
    content = {
        "operator_summary": "Review parser behavior for schema drift.",
        "impacts": ["Parser assumptions may need review."],
        "normalization_suggestions": ["Update normalization mapping."],
        "test_case_suggestions": ["Add a previous/current fixture test."],
    }
    content.update(overrides)

    return json.dumps(content)


def analyze(classified_changes: list[dict], content: str | None = None) -> dict:
    provider = OpenAICompatibleLLMProvider(
        api_key="test-key",
        model="test-model",
        client=FakeClient(content or fake_llm_content()),
    )

    return provider.analyze_diff(
        previous_schema_hash="previous-hash",
        current_schema_hash="current-hash",
        classified_changes=classified_changes,
    )


def test_openai_compatible_provider_returns_analysis_dict_with_required_keys() -> None:
    analysis = analyze(
        [
            {
                "change_type": "field_added",
                "path": "name",
                "previous": None,
                "current": field("name", ["string"]),
                "severity": "low",
            }
        ]
    )

    assert set(analysis) == {
        "provider",
        "previous_schema_hash",
        "current_schema_hash",
        "change_count",
        "severity_counts",
        "overall_severity",
        "operator_summary",
        "representative_changes",
        "impacts",
        "normalization_suggestions",
        "test_case_suggestions",
    }
    assert analysis["provider"] == "openai-compatible"
    assert analysis["previous_schema_hash"] == "previous-hash"
    assert analysis["current_schema_hash"] == "current-hash"
    assert analysis["change_count"] == 1
    assert set(analysis["severity_counts"]) == {"high", "medium", "low"}


def test_openai_compatible_provider_uses_llm_operator_facing_fields() -> None:
    analysis = analyze(
        [],
        fake_llm_content(
            operator_summary="No risky changes found.",
            impacts=["No immediate pipeline impact."],
            normalization_suggestions=["Keep current mapping."],
            test_case_suggestions=["Keep no-drift regression coverage."],
        ),
    )

    assert analysis["operator_summary"] == "No risky changes found."
    assert analysis["impacts"] == ["No immediate pipeline impact."]
    assert analysis["normalization_suggestions"] == ["Keep current mapping."]
    assert analysis["test_case_suggestions"] == ["Keep no-drift regression coverage."]


def test_openai_compatible_provider_keeps_deterministic_fields_from_input() -> None:
    analysis = analyze(
        [
            {
                "change_type": "type_changed",
                "path": "price",
                "previous": ["integer"],
                "current": ["object"],
                "severity": "high",
            }
        ],
        fake_llm_content(
            provider="malicious-provider",
            previous_schema_hash="wrong-previous",
            current_schema_hash="wrong-current",
            change_count=99,
            severity_counts={"high": 0, "medium": 0, "low": 0},
            overall_severity="none",
            representative_changes=[
                {
                    "severity": "low",
                    "change_type": "field_added",
                    "path": "fake",
                }
            ],
        ),
    )

    assert analysis["provider"] == "openai-compatible"
    assert analysis["previous_schema_hash"] == "previous-hash"
    assert analysis["current_schema_hash"] == "current-hash"
    assert analysis["change_count"] == 1
    assert analysis["severity_counts"] == {"high": 1, "medium": 0, "low": 0}
    assert analysis["overall_severity"] == "high"
    assert analysis["representative_changes"] == [
        {
            "severity": "high",
            "change_type": "type_changed",
            "path": "price",
            "previous_types": ["integer"],
            "current_types": ["object"],
        }
    ]


def test_openai_compatible_provider_returns_high_overall_severity() -> None:
    analysis = analyze(
        [
            {
                "change_type": "type_changed",
                "path": "price",
                "previous": ["integer"],
                "current": ["object"],
                "severity": "high",
            },
            {
                "change_type": "field_added",
                "path": "price.final",
                "previous": None,
                "current": field("price.final", ["integer"]),
                "severity": "low",
            },
        ]
    )

    assert analysis["overall_severity"] == "high"
    assert analysis["severity_counts"] == {"high": 1, "medium": 0, "low": 1}


def test_openai_compatible_provider_returns_medium_overall_severity() -> None:
    analysis = analyze(
        [
            {
                "change_type": "nullability_changed",
                "path": "description",
                "previous": False,
                "current": True,
                "severity": "medium",
            }
        ]
    )

    assert analysis["overall_severity"] == "medium"
    assert analysis["severity_counts"] == {"high": 0, "medium": 1, "low": 0}


def test_openai_compatible_provider_returns_low_overall_severity() -> None:
    analysis = analyze(
        [
            {
                "change_type": "field_added",
                "path": "name",
                "previous": None,
                "current": field("name", ["string"]),
                "severity": "low",
            }
        ]
    )

    assert analysis["overall_severity"] == "low"
    assert analysis["severity_counts"] == {"high": 0, "medium": 0, "low": 1}


def test_openai_compatible_provider_returns_none_overall_severity() -> None:
    analysis = analyze([])

    assert analysis["change_count"] == 0
    assert analysis["overall_severity"] == "none"
    assert analysis["severity_counts"] == {"high": 0, "medium": 0, "low": 0}
    assert analysis["representative_changes"] == []


def test_openai_compatible_provider_rejects_unknown_severity() -> None:
    with pytest.raises(ValueError, match="Unknown severity"):
        analyze(
            [
                {
                    "change_type": "field_added",
                    "path": "name",
                    "previous": None,
                    "current": field("name", ["string"]),
                    "severity": "critical",
                }
            ]
        )


def test_openai_compatible_provider_rejects_invalid_json_response() -> None:
    with pytest.raises(LLMResponseError, match="JSON object") as exc_info:
        analyze([], "not-json SECRET_SHOULD_NOT_LEAK")

    assert "SECRET_SHOULD_NOT_LEAK" not in str(exc_info.value)


@pytest.mark.parametrize(
    "content",
    [
        '["not", "object"]',
        '"not object"',
        "null",
        "123",
        "true",
    ],
)
def test_openai_compatible_provider_rejects_non_object_json_response(
    content,
) -> None:
    with pytest.raises(LLMResponseError, match="JSON object"):
        analyze([], content)


def test_openai_compatible_provider_falls_back_for_missing_or_wrong_field_types() -> (
    None
):
    analysis = analyze(
        [],
        json.dumps(
            {
                "operator_summary": ["not a string"],
                "impacts": "not a list",
            }
        ),
    )

    assert analysis["operator_summary"] == ""
    assert analysis["impacts"] == []
    assert analysis["normalization_suggestions"] == []
    assert analysis["test_case_suggestions"] == []


def test_openai_compatible_provider_ignores_llm_representative_changes() -> None:
    analysis = analyze(
        [
            {
                "change_type": "field_removed",
                "path": "price_overview",
                "previous": field("price_overview", ["object"]),
                "current": None,
                "severity": "high",
            }
        ],
        fake_llm_content(
            representative_changes=[
                {
                    "severity": "low",
                    "change_type": "field_added",
                    "path": "llm_supplied_path",
                }
            ]
        ),
    )

    assert analysis["representative_changes"] == [
        {
            "severity": "high",
            "change_type": "field_removed",
            "path": "price_overview",
        }
    ]


def test_openai_compatible_provider_does_not_mutate_classified_changes() -> None:
    classified_changes = [
        {
            "change_type": "field_added",
            "path": "name",
            "previous": None,
            "current": field("name", ["string"]),
            "severity": "low",
        }
    ]
    original_changes = copy.deepcopy(classified_changes)

    analyze(classified_changes)

    assert classified_changes == original_changes


def test_openai_compatible_provider_passes_model_messages_and_temperature() -> None:
    client = FakeClient(fake_llm_content())
    provider = OpenAICompatibleLLMProvider(
        api_key="test-key",
        model="deepseek-chat",
        client=client,
    )
    classified_changes = [
        {
            "change_type": "field_removed",
            "path": "currency",
            "previous": field("currency", ["string"]),
            "current": None,
            "severity": "high",
        }
    ]

    provider.analyze_diff(
        previous_schema_hash="previous-hash",
        current_schema_hash="current-hash",
        classified_changes=classified_changes,
    )

    [call] = client.chat.completions.calls
    assert call["model"] == "deepseek-chat"
    assert call["temperature"] == 0
    assert [message["role"] for message in call["messages"]] == ["system", "user"]

    system_prompt = call["messages"][0]["content"]
    assert "Return only a JSON object" in system_prompt
    assert "Do not return Markdown fenced code blocks" in system_prompt
    assert "allowed fields" in system_prompt
    assert "operator_summary" in system_prompt
    assert "impacts" in system_prompt
    assert "normalization_suggestions" in system_prompt
    assert "test_case_suggestions" in system_prompt
    assert "Do not write or overwrite deterministic fields" in system_prompt
    assert "previous_schema_hash" in system_prompt
    assert "current_schema_hash" in system_prompt
    assert "change_count" in system_prompt
    assert "severity_counts" in system_prompt
    assert "overall_severity" in system_prompt
    assert "representative_changes" in system_prompt
    assert "Do not perform schema extraction" in system_prompt
    assert "schema diffing" in system_prompt
    assert "severity judgment" in system_prompt
    assert "at least 1 item" in system_prompt
    assert "2 to 5 concrete items" in system_prompt
    assert "Empty arrays are allowed only when there is no drift" in system_prompt
    assert "affected path" in system_prompt
    assert "Avoid generic fallback wording" in system_prompt

    assert json.loads(call["messages"][1]["content"]) == {
        "previous_schema_hash": "previous-hash",
        "current_schema_hash": "current-hash",
        "classified_changes": classified_changes,
    }
    assert call["messages"][1]["content"] == json.dumps(
        {
            "previous_schema_hash": "previous-hash",
            "current_schema_hash": "current-hash",
            "classified_changes": classified_changes,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def test_openai_compatible_provider_does_not_create_client_when_injected(
    monkeypatch,
) -> None:
    def fail_openai_constructor(**kwargs):
        raise AssertionError("OpenAI constructor should not be called")

    monkeypatch.setattr(openai_compatible.openai, "OpenAI", fail_openai_constructor)

    provider = OpenAICompatibleLLMProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://api.example.test/v1",
        client=FakeClient(fake_llm_content()),
    )
    analysis = provider.analyze_diff(
        previous_schema_hash="previous-hash",
        current_schema_hash="current-hash",
        classified_changes=[],
    )

    assert analysis["provider"] == "openai-compatible"


def test_openai_compatible_provider_passes_base_url_to_created_client(
    monkeypatch,
) -> None:
    created_clients = []

    class FakeOpenAI:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            self.chat = FakeChat(fake_llm_content())
            created_clients.append(self)

    monkeypatch.setattr(openai_compatible.openai, "OpenAI", FakeOpenAI)

    provider = OpenAICompatibleLLMProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://api.example.test/v1",
    )
    provider.analyze_diff(
        previous_schema_hash="previous-hash",
        current_schema_hash="current-hash",
        classified_changes=[],
    )

    [created_client] = created_clients
    assert created_client.kwargs == {
        "api_key": "test-key",
        "base_url": "https://api.example.test/v1",
    }


def test_openai_compatible_provider_omits_none_base_url_for_created_client(
    monkeypatch,
) -> None:
    created_clients = []

    class FakeOpenAI:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            self.chat = FakeChat(fake_llm_content())
            created_clients.append(self)

    monkeypatch.setattr(openai_compatible.openai, "OpenAI", FakeOpenAI)

    provider = OpenAICompatibleLLMProvider(
        api_key="test-key",
        model="test-model",
    )
    provider.analyze_diff(
        previous_schema_hash="previous-hash",
        current_schema_hash="current-hash",
        classified_changes=[],
    )

    [created_client] = created_clients
    assert created_client.kwargs == {"api_key": "test-key"}
