from typing import TypedDict

from driftlens.schema.types import (
    ChangeType,
    OverallSeverity,
    SchemaValueType,
    Severity,
    SeverityCounts,
)


class BaseRepresentativeChange(TypedDict):
    severity: Severity
    change_type: ChangeType
    path: str


class TypeChangedRepresentativeChange(BaseRepresentativeChange):
    previous_types: list[SchemaValueType]
    current_types: list[SchemaValueType]


type RepresentativeChange = BaseRepresentativeChange | TypeChangedRepresentativeChange
type LLMTextItems = list[object]


class LLMAnalysis(TypedDict):
    provider: str
    previous_schema_hash: str
    current_schema_hash: str
    change_count: int
    severity_counts: SeverityCounts
    overall_severity: OverallSeverity
    operator_summary: str
    representative_changes: list[RepresentativeChange]
    impacts: LLMTextItems
    normalization_suggestions: LLMTextItems
    test_case_suggestions: LLMTextItems
