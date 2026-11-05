# Part-1A: Deterministic Asset Allocation API

Part-1A is a stateless FastAPI service that returns an equity and fixed-income allocation using a documented deterministic rule. It is an educational rule-based estimate, not individualized financial advice or a guarantee of returns.

## Requirements

- Python 3.11 or newer
- Installable project dependencies from `pyproject.toml`

## Install and run

From the `Part-1A` directory in PowerShell:

```powershell
python -m pip install -e ".[test]"
python -m uvicorn asset_allocation.app:app --reload
```

The service listens at `http://127.0.0.1:8000`. Interactive API documentation is at `http://127.0.0.1:8000/docs`.

## API contract

Send `POST /allocation` with `Content-Type: application/json`:

```json
{
  "age": 40,
  "horizon_years": 10,
  "risk_tolerance": 5
}
```

Successful response (`200`):

```json
{
  "equities_percent": 60,
  "fixed_income_percent": 40
}
```

The equity percentage is calculated as:

```text
clamp(100 - age + 4 * (risk_tolerance - 5) + 2 * (horizon_years - 10), 0, 100)
```

Fixed income is `100 - equities_percent`. The formula currently yields integer values for integer inputs; results are clamped to `0–100`.

| Input | Accepted values |
|---|---:|
| `age` | Integer, 18–100 |
| `horizon_years` | Integer, 1–80 |
| `risk_tolerance` | Integer, 1–10 |

The JSON object must contain exactly those three fields. Values must be JSON integers: booleans, strings, floats, nulls, and implicit conversions are rejected. Age and horizon are validated independently.

### Errors and request limits

- `400 invalid_json`: malformed JSON, invalid UTF-8, or non-standard JSON constants.
- `413 request_too_large`: request body exceeds 16 KiB.
- `415 unsupported_media_type`: content type is not JSON with optional UTF-8 charset, or content encoding is not absent/`identity`.
- `422 invalid_request`: invalid object shape, duplicate keys, wrong types, or out-of-range values.

Errors use a JSON object with an `error` containing a stable `code` and explanatory `message`; no allocation is returned on errors.

## Tests and harness

Run unit and API contract tests:

```powershell
python -m pytest
```

Run the local lint, security, and test pipeline from the `Part-1A` directory:

```powershell
python .harness/runner.py
```

The runner resolves source and test paths relative to itself. Ruff and Bandit must be available in the active environment for the full harness run.

## Specification and evidence

The feature details are in [speckit.spec.md](./speckit.spec.md), with supporting constitution, clarification, plan, and tasks files in this folder. [harness.log.md](./harness.log.md) records the most recent validation evidence. The `evidence/` directory contains the preserved initial-generation snapshot.
