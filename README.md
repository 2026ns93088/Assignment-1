# Assignment-1

## Asset Allocation API

A deterministic, stateless HTTP API that returns an equity and fixed-income split as a rule-based estimate. It is not individualized financial advice and does not guarantee returns.

### Allocation rule

For integer inputs, the API calculates:

```text
equities_percent = clamp(
    100 - age + 4 * (risk_tolerance - 5) + 2 * (horizon_years - 10),
    0,
    100,
)
fixed_income_percent = 100 - equities_percent
```

`age` must be from 18 through 100, `horizon_years` from 1 through 80, and `risk_tolerance` from 1 through 10. The current integer formula always yields an integer; the specification's half-up rounding rule therefore does not alter current results. Age and horizon are validated independently; no additional lifespan assumption is applied.

### Run locally

```powershell
python -m pip install -e ".[test]"
python -m uvicorn asset_allocation.app:app --reload
```

The API listens at `http://127.0.0.1:8000`. Interactive API documentation is available at `/docs`.

### Request and response

Send `POST /allocation` with `Content-Type: application/json`:

```json
{
  "age": 40,
  "horizon_years": 10,
  "risk_tolerance": 5
}
```

Successful requests return HTTP `200`:

```json
{
  "equities_percent": 60,
  "fixed_income_percent": 40
}
```

Only the three documented request keys are accepted. Values must be JSON integers (booleans are rejected), with no coercion or defaults. Duplicate keys, malformed/non-standard JSON, and invalid UTF-8 are rejected. The request body is limited to 16 KiB. Only `application/json` with no charset or UTF-8 charset is accepted; `Content-Encoding` must be absent or `identity`.

Malformed JSON returns HTTP `400`:

```json
{
  "error": {
    "code": "invalid_json",
    "message": "Request body must be valid JSON."
  }
}
```

Invalid request shape or values return HTTP `422` with `code: "invalid_request"`. Unsupported media type or content encoding returns HTTP `415` with `code: "unsupported_media_type"`. Oversized request bodies return HTTP `413` with `code: "request_too_large"`. Error messages are stable; when multiple validation issues exist, one is reported using the order documented in the feature specification.

### Tests

```powershell
python -m pytest
```