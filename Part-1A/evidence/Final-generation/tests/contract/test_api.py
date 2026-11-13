import json

import pytest
from fastapi.testclient import TestClient

from asset_allocation.app import app
from asset_allocation.validation import MAX_REQUEST_BODY_BYTES

client = TestClient(app)
VALID_REQUEST = {
    "age": 40,
    "horizon_years": 10,
    "risk_tolerance": 5,
}


def test_valid_request_returns_exact_success_contract() -> None:
    response = client.post("/allocation", json=VALID_REQUEST)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "equities_percent": 60,
        "fixed_income_percent": 40,
    }
    assert set(response.json()) == {"equities_percent", "fixed_income_percent"}


def test_repeated_requests_have_semantically_identical_responses() -> None:
    first = client.post("/allocation", json=VALID_REQUEST)
    second = client.post("/allocation", json=VALID_REQUEST)

    assert (first.status_code, first.json()) == (second.status_code, second.json())


@pytest.mark.parametrize(
    ("body", "status_code", "error"),
    [
        (
            b"",
            400,
            {
                "code": "invalid_json",
                "message": "Request body must be valid JSON.",
            },
        ),
        (
            b"{",
            400,
            {
                "code": "invalid_json",
                "message": "Request body must be valid JSON.",
            },
        ),
        (
            b'{"age":40,"horizon_years":10,"risk_tolerance":5,"extra":1}',
            422,
            {
                "code": "invalid_request",
                "message": "Unexpected field: extra.",
            },
        ),
        (
            b'{"horizon_years":10,"risk_tolerance":5}',
            422,
            {
                "code": "invalid_request",
                "message": "Missing required field: age.",
            },
        ),
        (
            b'{"age":true,"horizon_years":10,"risk_tolerance":5}',
            422,
            {
                "code": "invalid_request",
                "message": "age must be an integer.",
            },
        ),
        (
            b'{"age":40,"horizon_years":10.0,"risk_tolerance":5}',
            422,
            {
                "code": "invalid_request",
                "message": "horizon_years must be an integer.",
            },
        ),
        (
            b'{"age":17,"horizon_years":10,"risk_tolerance":5}',
            422,
            {
                "code": "invalid_request",
                "message": "age must be between 18 and 100.",
            },
        ),
        (
            b'{"age":40,"horizon_years":10,"risk_tolerance":11}',
            422,
            {
                "code": "invalid_request",
                "message": "risk_tolerance must be between 1 and 10.",
            },
        ),
        (
            b'{"age":NaN,"horizon_years":10,"risk_tolerance":5}',
            400,
            {
                "code": "invalid_json",
                "message": "Request body must be valid JSON.",
            },
        ),
        (
            b'{"age":40,"age":41,"horizon_years":10,"risk_tolerance":5}',
            422,
            {
                "code": "invalid_request",
                "message": "Duplicate JSON object key: age.",
            },
        ),
    ],
)
def test_error_responses_follow_stable_contract(
    body: bytes,
    status_code: int,
    error: dict[str, str],
) -> None:
    response = client.post(
        "/allocation",
        content=body,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"error": error}
    assert "equities_percent" not in response.json()
    assert "fixed_income_percent" not in response.json()


@pytest.mark.parametrize(
    ("headers", "expected_message"),
    [
        ({}, "Content-Type must be application/json with UTF-8 encoding."),
        (
            {"content-type": "text/plain"},
            "Content-Type must be application/json with UTF-8 encoding.",
        ),
        (
            {"content-type": "application/json; charset=iso-8859-1"},
            "Content-Type must be application/json with UTF-8 encoding.",
        ),
        (
            {
                "content-type": "application/json",
                "content-encoding": "gzip",
            },
            "Content-Encoding must be absent or identity.",
        ),
    ],
)
def test_unsupported_media_inputs_are_rejected(
    headers: dict[str, str],
    expected_message: str,
) -> None:
    response = client.post("/allocation", content=b"{}", headers=headers)

    assert response.status_code == 415
    assert response.json() == {
        "error": {
            "code": "unsupported_media_type",
            "message": expected_message,
        }
    }


def test_request_body_size_is_limited() -> None:
    body = b" " * (MAX_REQUEST_BODY_BYTES + 1)
    response = client.post(
        "/allocation",
        content=body,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json() == {
        "error": {
            "code": "request_too_large",
            "message": f"Request body must not exceed {MAX_REQUEST_BODY_BYTES} bytes.",
        }
    }


def test_boundary_requests_are_accepted() -> None:
    for age, horizon, risk in (
        (18, 1, 1),
        (100, 80, 10),
    ):
        response = client.post(
            "/allocation",
            json={
                "age": age,
                "horizon_years": horizon,
                "risk_tolerance": risk,
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["equities_percent"] + result["fixed_income_percent"] == 100


def test_non_object_json_is_invalid_request() -> None:
    response = client.post(
        "/allocation",
        content=json.dumps([]),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
