from typing import Literal, TypedDict


type SchemaValueType = Literal[
    "null",
    "boolean",
    "integer",
    "number",
    "string",
    "array",
    "object",
    "unknown",
]


class SchemaField(TypedDict):
    path: str
    types: list[SchemaValueType]
    nullable: bool


class ObservedSchema(TypedDict):
    fields: list[SchemaField]


type ChangeType = Literal[
    "field_added",
    "field_removed",
    "type_changed",
    "nullability_changed",
]

type Severity = Literal["high", "medium", "low"]
type OverallSeverity = Literal["high", "medium", "low", "none"]


class SeverityCounts(TypedDict):
    high: int
    medium: int
    low: int


class FieldAddedChange(TypedDict):
    change_type: Literal["field_added"]
    path: str
    previous: None
    current: SchemaField


class FieldRemovedChange(TypedDict):
    change_type: Literal["field_removed"]
    path: str
    previous: SchemaField
    current: None


class TypeChangedChange(TypedDict):
    change_type: Literal["type_changed"]
    path: str
    previous: list[SchemaValueType]
    current: list[SchemaValueType]


class NullabilityChangedChange(TypedDict):
    change_type: Literal["nullability_changed"]
    path: str
    previous: bool
    current: bool


type SchemaChange = (
    FieldAddedChange | FieldRemovedChange | TypeChangedChange | NullabilityChangedChange
)


class ClassifiedFieldAddedChange(FieldAddedChange):
    severity: Severity


class ClassifiedFieldRemovedChange(FieldRemovedChange):
    severity: Severity


class ClassifiedTypeChangedChange(TypeChangedChange):
    severity: Severity


class ClassifiedNullabilityChangedChange(NullabilityChangedChange):
    severity: Severity


type ClassifiedSchemaChange = (
    ClassifiedFieldAddedChange
    | ClassifiedFieldRemovedChange
    | ClassifiedTypeChangedChange
    | ClassifiedNullabilityChangedChange
)
