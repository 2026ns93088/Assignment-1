# Technical Architecture and Implementation Plan

**Feature**: Deterministic Asset Allocation API  
**Inputs**: `speckit.spec.md`, `speckit.constitution.md`, `speckit.clarify.md`  
**Status**: Contract decisions recorded in `speckit.spec.md`; implementation may proceed.

## 1. Overview

Implement a stateless Python HTTP API that validates a strict JSON request, applies the documented allocation formula, and returns a stable JSON portfolio split. The calculation is a pure function; HTTP parsing and validation are kept separate from it. No user data is persisted and no market data or external decision service is used.

## 2. Architecture

### Request flow

1. The HTTP route accepts `POST /allocation`.
2. The transport layer reads and parses the request body as JSON. Parsing failures use the malformed-JSON response defined in the specification.
3. The request validation layer requires an object with exactly `age`, `horizon_years`, and `risk_tolerance`. It validates exact integer types (rejecting booleans), required ranges, missing keys, and unknown keys without coercing values.
4. The allocation domain function calculates:

   `equities = clamp(100 - age + 4 * (risk_tolerance - 5) + 2 * (horizon_years - 10), 0, 100)`

   The current formula has integer inputs and integer coefficients, so its result is always integral; the documented half-up rule is retained but has no effect for current inputs.
5. The response layer returns `equities_percent` and `fixed_income_percent = 100 - equities_percent` as JSON integers.

### Component responsibilities

- **API/transport**: route, request-body parsing, HTTP status codes, JSON serialization, and response content type.
- **Validation**: explicit schema and domain checks; map invalid requests to the documented stable error envelope.
- **Domain**: pure allocation calculation, no framework or I/O dependencies.
- **Tests**: unit tests for the pure domain function and HTTP-level contract tests for request validation and serialization.

### Selected implementation choices

- Use **FastAPI** for the HTTP route and **pytest** for tests. Keep calculation and validation behavior explicit rather than relying on coercive defaults.
- Parse request bytes explicitly before validation so malformed JSON and valid-but-invalid JSON map to the specified `400` and `422` response contracts.
- Reject duplicate keys, non-standard JSON constants, and invalid UTF-8; accept only UTF-8 JSON with an absent or identity content encoding.
- Limit the body to `16384` bytes and use the explicit `413` response for oversized inputs.
- Treat age and horizon bounds independently, return only the first validation failure in the specified deterministic order, and do not expose a rule-version field.
- Keep runtime dependencies limited to the web framework and its required dependencies; use the standard library for JSON handling and arithmetic.

These decisions are recorded as requirements in `speckit.spec.md`.

## 3. Data Contracts

### Request

```json
{
  "age": 40,
  "horizon_years": 10,
  "risk_tolerance": 5
}
```

The object must contain exactly those keys. Values must be JSON integers, with bounds `18–100`, `1–80`, and `1–10`, respectively. No defaults or coercion are permitted.

### Success response

```json
{
  "equities_percent": 60,
  "fixed_income_percent": 40
}
```

The two integer percentages must be in `0–100` and sum to `100`.

### Errors

- Malformed JSON: HTTP `400`, code `invalid_json`, fixed message from FR-007.
- Valid JSON with an invalid shape or values: HTTP `422`, code `invalid_request`, non-empty stable message.

Do not include allocation fields in an error response.

## 4. Proposed Project Structure

```text
src/
  asset_allocation/
    __init__.py
    app.py            # FastAPI app and route registration
    api.py            # HTTP endpoint and request/response mapping
    errors.py         # Stable API error contract
    validation.py     # Strict request parsing and domain validation
    allocation.py     # Pure allocation function
tests/
  unit/
    test_allocation.py
  contract/
    test_api.py
pyproject.toml        # Project metadata, dependencies, and test configuration
README.md             # Run instructions and API contract
```

Keep the final layout consistent with any repository or assignment structure introduced before implementation. Do not mix project implementation files with the Part-1A planning documents unless explicitly requested.

## 5. Implementation Sequence

1. **Freeze public-contract decisions** in `speckit.spec.md`; the clarification questions have been resolved in `speckit.clarify.md`.
2. **Create the minimal Python project** with the chosen framework, test runner, and documented local run command.
3. **Implement and test the pure calculation** with the approved formula, clamping, complement invariant, and representative values.
4. **Implement strict request validation** for object shape, exact integer types, ranges, and any resolved duplicate-key/JSON parsing rules.
5. **Add the HTTP endpoint and error mapping** for the confirmed route, media type, malformed JSON, validation failures, and successful response.
6. **Write public API documentation** including formula, field names, bounds, examples, error contract, and financial-scope disclaimer.
7. **Run targeted tests and quality checks**; verify boundary, invalid-input, determinism, output-shape, and sum-to-100 requirements.

## 6. Verification Plan

### Domain unit tests

- Baseline: `(age=40, horizon_years=10, risk_tolerance=5)` yields `(60, 40)`.
- Risk adjustment: risk `1` yields `(44, 56)` and risk `10` yields `(80, 20)` for age `40`, horizon `10`.
- Upper clamp: `(18, 80, 10)` yields `(100, 0)`.
- Lower clamp: `(100, 1, 1)` yields `(0, 100)`.
- For all tested valid combinations, both values are integers in `0–100` and sum to `100`.
- Repeated identical inputs produce identical domain results.

### HTTP contract tests

- Valid request returns HTTP `200`, JSON content type, exactly the two documented success keys, and expected values.
- Malformed and empty bodies return the specified `400` error shape.
- Non-object JSON, missing keys, unknown keys, wrong JSON types, booleans, and out-of-range values return HTTP `422` with `invalid_request` and no allocation.
- Verify lower and upper bounds are accepted and values immediately outside each bound are rejected.
- Verify multiple identical requests produce semantically identical responses.
- Test duplicate keys, content type, invalid encoding, and oversized bodies according to the decisions recorded in the specification.

### Quality checks

- Run the focused test suite for the changed package.
- Run the project's configured formatter, linter, and type checker if added or required by repository conventions.
- Confirm documentation matches the implemented route and response behavior.

## 7. Non-Functional Constraints

- Calculation must be deterministic and independent of network access, time, randomness, persistence, or process state.
- The core calculation must be importable and testable without starting the HTTP server.
- Keep dependencies minimal and avoid logging request bodies or unnecessary personal input values.
- Do not claim that the output predicts returns, guarantees performance, or constitutes individualized financial advice.

## 8. Resolved Contract Decisions

The decisions have been recorded as functional requirements FR-012–FR-018 in `speckit.spec.md`. The implementation must conform to those requirements: independent age/horizon bounds, duplicate-key rejection, UTF-8 JSON only, a 16 KiB request limit, deterministic validation precedence, no public rule version, and semantic JSON determinism. Half-up rounding remains documented even though it has no effect for the current integer formula.

## 9. Risks and Mitigations

- **Framework defaults may not match the strict contract**: Own parsing, exact type checks, and error mapping explicitly, then cover them with HTTP contract tests.
- **Changes to the selected transport contract can affect clients**: Treat the response codes, request limit, and validation ordering in the specification as compatibility commitments.
- **Financial interpretation risk**: Publish the rule as a deterministic software estimate, include its assumptions and limitations, and avoid suitability or outcome claims.
