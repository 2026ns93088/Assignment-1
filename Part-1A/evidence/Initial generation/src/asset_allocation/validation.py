"""Strict JSON parsing and allocation request validation."""

import json
from dataclasses import dataclass
from typing import Any

from asset_allocation.errors import APIError

MAX_REQUEST_BODY_BYTES = 16 * 1024
REQUEST_FIELDS = ("age", "horizon_years", "risk_tolerance")
FIELD_BOUNDS = {
    "age": (18, 100),
    "horizon_years": (1, 80),
    "risk_tolerance": (1, 10),
}


@dataclass(frozen=True)
class AllocationRequest:
    age: int
    horizon_years: int
    risk_tolerance: int


class _DuplicateJSONKeyError(ValueError):
    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


class _NonStandardJSONConstantError(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKeyError(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise _NonStandardJSONConstantError(value)


def parse_allocation_request(body: bytes) -> AllocationRequest:
    """Parse strict UTF-8 JSON and validate its exact schema and value ranges."""
    try:
        payload = json.loads(
            body.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except _DuplicateJSONKeyError as error:
        raise APIError(
            422,
            "invalid_request",
            f"Duplicate JSON object key: {error.key}.",
        ) from error
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        _NonStandardJSONConstantError,
        RecursionError,
    ) as error:
        raise APIError(
            400,
            "invalid_json",
            "Request body must be valid JSON.",
        ) from error

    if not isinstance(payload, dict):
        raise APIError(
            422,
            "invalid_request",
            "Request body must be a JSON object.",
        )

    missing_fields = [field for field in REQUEST_FIELDS if field not in payload]
    if missing_fields:
        raise APIError(
            422,
            "invalid_request",
            f"Missing required field: {missing_fields[0]}.",
        )

    unexpected_fields = sorted(set(payload) - set(REQUEST_FIELDS))
    if unexpected_fields:
        raise APIError(
            422,
            "invalid_request",
            f"Unexpected field: {unexpected_fields[0]}.",
        )

    for field in REQUEST_FIELDS:
        value = payload[field]
        if type(value) is not int:
            raise APIError(
                422,
                "invalid_request",
                f"{field} must be an integer.",
            )

        minimum, maximum = FIELD_BOUNDS[field]
        if not minimum <= value <= maximum:
            raise APIError(
                422,
                "invalid_request",
                f"{field} must be between {minimum} and {maximum}.",
            )

    return AllocationRequest(
        age=payload["age"],
        horizon_years=payload["horizon_years"],
        risk_tolerance=payload["risk_tolerance"],
    )
