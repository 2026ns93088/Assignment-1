"""FastAPI application setup."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from asset_allocation.api import router
from asset_allocation.errors import APIError

app = FastAPI(
    title="Deterministic Asset Allocation API",
    description=(
        "Returns a deterministic, rule-based allocation estimate. "
        "It is not individualized financial advice or a guarantee of returns."
    ),
)
app.include_router(router)


@app.exception_handler(APIError)
async def handle_api_error(request: Request, error: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
            }
        },
    )
