import json

import pytest

from asset_allocation.errors import APIError
from asset_allocation.validation import parse_allocation_request


@pytest.mark.parametrize(
    ("field", "minimum", "maximum"),
    [
        ("age", 18, 100),
        ("horizon_years", 1, 80),
        ("risk_tolerance", 1, 10),
    ],
)
def test_field_bounds_are_inclusive(field: str, minimum: int, maximum: int) -> None:
    payload = {"age": 40, "horizon_years": 10, "risk_tolerance": 5}
    payload[field] = minimum
    assert getattr(parse_allocation_request(json.dumps(payload).encode()), field) == minimum

    payload[field] = maximum
    assert getattr(parse_allocation_request(json.dumps(payload).encode()), field) == maximum


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("age", 17),
        ("age", 101),
        ("horizon_years", 0),
        ("horizon_years", 81),
        ("risk_tolerance", 0),
        ("risk_tolerance", 11),
        ("age", "40"),
        ("horizon_years", 10.0),
        ("risk_tolerance", True),
        ("risk_tolerance", False),
        ("age", None),
        ("horizon_years", []),
        ("risk_tolerance", {}),
    ],
)
def test_invalid_field_values_are_rejected(field: str, invalid_value: object) -> None:
    payload: dict[str, object] = {
        "age": 40,
        "horizon_years": 10,
        "risk_tolerance": 5,
    }
    payload[field] = invalid_value

    with pytest.raises(APIError) as error:
        parse_allocation_request(json.dumps(payload).encode())

    assert error.value.status_code == 422
    assert error.value.code == "invalid_request"
    assert error.value.message


@pytest.mark.parametrize(
    ("body", "expected_status", "expected_code", "expected_message"),
    [
        (b"", 400, "invalid_json", "Request body must be valid JSON."),
        (b'{"age":', 400, "invalid_json", "Request body must be valid JSON."),
        (b"\xff", 400, "invalid_json", "Request body must be valid JSON."),
        (
            b'{"age":NaN,"horizon_years":10,"risk_tolerance":5}',
            400,
            "invalid_json",
            "Request body must be valid JSON.",
        ),
        (
            b'{"age":Infinity,"horizon_years":10,"risk_tolerance":5}',
            400,
            "invalid_json",
            "Request body must be valid JSON.",
        ),
        (
            b'{"age":-Infinity,"horizon_years":10,"risk_tolerance":5}',
            400,
            "invalid_json",
            "Request body must be valid JSON.",
        ),
        (
            b'{"age":40,"age":41,"horizon_years":10,"risk_tolerance":5}',
            422,
            "invalid_request",
            "Duplicate JSON object key: age.",
        ),
        (
            b'{"age":40,"horizon_years":10,"risk_tolerance":5,"unknown":0}',
            422,
            "invalid_request",
            "Unexpected field: unknown.",
        ),
        (
            b'{"age":false,"horizon_years":0,"risk_tolerance":5}',
            422,
            "invalid_request",
            "age must be an integer.",
        ),
    ],
)
def test_json_and_schema_errors_are_stable(
    body: bytes,
    expected_status: int,
    expected_code: str,
    expected_message: str,
) -> None:
    with pytest.raises(APIError) as error:
        parse_allocation_request(body)

    assert error.value.status_code == expected_status
    assert error.value.code == expected_code
    assert error.value.message == expected_message


@pytest.mark.parametrize("body", [b"[]", b"null", b"42", b'"text"'])
def test_non_object_json_is_rejected(body: bytes) -> None:
    with pytest.raises(APIError) as error:
        parse_allocation_request(body)

    assert error.value.status_code == 422
    assert error.value.code == "invalid_request"
    assert error.value.message == "Request body must be a JSON object."


def test_missing_fields_are_reported_in_schema_order() -> None:
    with pytest.raises(APIError) as error:
        parse_allocation_request(b'{"horizon_years":10}')

    assert error.value.message == "Missing required field: age."
