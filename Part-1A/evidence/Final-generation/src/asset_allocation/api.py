"""HTTP route for the allocation API."""

import re

from fastapi import APIRouter, Request

from asset_allocation.allocation import allocate
from asset_allocation.errors import APIError
from asset_allocation.validation import MAX_REQUEST_BODY_BYTES, parse_allocation_request

router = APIRouter()
_JSON_CONTENT_TYPE = re.compile(
    r'application/json(?:\s*;\s*charset\s*=\s*"?utf-8"?)?',
    re.IGNORECASE,
)


def _validate_content_type(value: str | None) -> None:
    if value is None or _JSON_CONTENT_TYPE.fullmatch(value.strip()) is None:
        raise APIError(
            415,
            "unsupported_media_type",
            "Content-Type must be application/json with UTF-8 encoding.",
        )


def _validate_content_encoding(value: str | None) -> None:
    if value is not None and value.strip().lower() != "identity":
        raise APIError(
            415,
            "unsupported_media_type",
            "Content-Encoding must be absent or identity.",
        )


async def _read_limited_body(request: Request) -> bytes:
    chunks: list[bytes] = []
    total_bytes = 0
    async for chunk in request.stream():
        total_bytes += len(chunk)
        if total_bytes > MAX_REQUEST_BODY_BYTES:
            raise APIError(
                413,
                "request_too_large",
                f"Request body must not exceed {MAX_REQUEST_BODY_BYTES} bytes.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/allocation")
async def create_allocation(request: Request) -> dict[str, int]:
    _validate_content_type(request.headers.get("content-type"))
    _validate_content_encoding(request.headers.get("content-encoding"))

    body = await _read_limited_body(request)
    allocation_request = parse_allocation_request(body)
    result = allocate(
        age=allocation_request.age,
        horizon_years=allocation_request.horizon_years,
        risk_tolerance=allocation_request.risk_tolerance,
    )
    return {
        "equities_percent": result.equities_percent,
        "fixed_income_percent": result.fixed_income_percent,
    }
