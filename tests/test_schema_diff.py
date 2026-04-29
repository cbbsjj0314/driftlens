from driftlens.schema.diff import diff_schemas


def field(path: str, types: list[str], nullable: bool = False) -> dict:
    return {"path": path, "types": types, "nullable": nullable}


def schema(fields: list[dict]) -> dict:
    return {"fields": fields}


def test_diff_schemas_detects_field_added() -> None:
    previous = schema([field("appid", ["integer"])])
    current = schema([field("appid", ["integer"]), field("name", ["string"])])

    assert diff_schemas(previous, current) == [
        {
            "change_type": "field_added",
            "path": "name",
            "previous": None,
            "current": field("name", ["string"]),
        }
    ]


def test_diff_schemas_detects_field_removed() -> None:
    previous = schema([field("appid", ["integer"]), field("currency", ["string"])])
    current = schema([field("appid", ["integer"])])

    assert diff_schemas(previous, current) == [
        {
            "change_type": "field_removed",
            "path": "currency",
            "previous": field("currency", ["string"]),
            "current": None,
        }
    ]


def test_diff_schemas_detects_type_changed() -> None:
    previous = schema([field("price", ["integer"])])
    current = schema([field("price", ["object"])])

    assert diff_schemas(previous, current) == [
        {
            "change_type": "type_changed",
            "path": "price",
            "previous": ["integer"],
            "current": ["object"],
        }
    ]


def test_diff_schemas_detects_nullability_changed() -> None:
    previous = schema([field("description", ["string"])])
    current = schema([field("description", ["null", "string"], nullable=True)])

    assert diff_schemas(previous, current) == [
        {
            "change_type": "nullability_changed",
            "path": "description",
            "previous": False,
            "current": True,
        },
    ]


def test_diff_schemas_sorts_results_deterministically() -> None:
    previous = schema(
        [
            field("z_removed", ["string"]),
            field("b_changed", ["integer"], nullable=True),
            field("a_same", ["string"]),
        ]
    )
    current = schema(
        [
            field("c_added", ["boolean"]),
            field("b_changed", ["object"]),
            field("a_same", ["string"]),
        ]
    )

    assert diff_schemas(previous, current) == [
        {
            "change_type": "nullability_changed",
            "path": "b_changed",
            "previous": True,
            "current": False,
        },
        {
            "change_type": "type_changed",
            "path": "b_changed",
            "previous": ["integer"],
            "current": ["object"],
        },
        {
            "change_type": "field_added",
            "path": "c_added",
            "previous": None,
            "current": field("c_added", ["boolean"]),
        },
        {
            "change_type": "field_removed",
            "path": "z_removed",
            "previous": field("z_removed", ["string"]),
            "current": None,
        },
    ]
