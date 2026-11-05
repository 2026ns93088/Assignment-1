# Feature Specification: Deterministic Asset Allocation API

**Feature Branch**: `001-asset-allocation-api`  
**Status**: Draft  
**Input**: Constitution at `constitution.md` and confirmed allocation policy

## User Scenarios & Testing

### User Story 1 - Get a rule-based portfolio allocation (Priority: P1)

As a client of the API, I want to submit my age, investment horizon, and risk tolerance and receive a predictable portfolio split, so that I can use a consistent allocation result in my application.

**Why this priority**: Returning a valid, reproducible allocation is the core purpose of the feature.

**Independent Test**: Submit a valid JSON request to `POST /allocation`; verify the status, response shape, formula result, and percentage sum.

**Acceptance Scenarios**:

1. **Given** a valid request with age `40`, horizon `10`, and risk tolerance `5`, **When** it is submitted, **Then** the API returns HTTP `200` and `{"equities_percent":60,"fixed_income_percent":40}`.
2. **Given** the same valid request is submitted more than once, **When** the allocation is calculated, **Then** every response has identical status and body.
3. **Given** any valid request, **When** the allocation is returned, **Then** `equities_percent` and `fixed_income_percent` are integers from `0` through `100` inclusive and sum to exactly `100`.
4. **Given** age `40`, horizon `10`, and risk tolerance `1`, **When** submitted, **Then** the API returns `{"equities_percent":44,"fixed_income_percent":56}`; with risk tolerance `10`, it returns `{"equities_percent":80,"fixed_income_percent":20}`.
5. **Given** age `18`, horizon `80`, and risk tolerance `10`, **When** submitted, **Then** the raw equity result is clamped to `100` and the API returns `{"equities_percent":100,"fixed_income_percent":0}`.
6. **Given** age `100`, horizon `1`, and risk tolerance `1`, **When** submitted, **Then** the raw equity result is clamped to `0` and the API returns `{"equities_percent":0,"fixed_income_percent":100}`.
7. **Given** any valid request, **When** its allocation is calculated, **Then** the equity percentage is the nearest integer to `clamp(100 - age + 4 * (risk_tolerance - 5) + 2 * (horizon_years - 10), 0, 100)`, with exact half-point ties rounded up, and the fixed-income percentage is `100 - equities_percent`.

### User Story 2 - Reject invalid or ambiguous input (Priority: P1)

As a client of the API, I want invalid requests to be rejected explicitly, so that malformed or out-of-domain data cannot silently produce a misleading allocation.

**Independent Test**: Submit malformed JSON, invalid JSON shapes, wrong types, missing or extra keys, and boundary/out-of-range values; verify the specified error response and that no allocation is returned.

**Acceptance Scenarios**:

1. **Given** a request body that is not valid JSON, **When** submitted, **Then** the API returns HTTP `400` with `{"error":{"code":"invalid_json","message":"Request body must be valid JSON."}}`.
2. **Given** valid JSON that is not an object, **When** submitted, **Then** the API returns HTTP `422` with error code `invalid_request` and does not return an allocation.
3. **Given** an object missing any required field or containing any unrecognized field, **When** submitted, **Then** the API returns HTTP `422` with error code `invalid_request` and does not return an allocation.
4. **Given** a required value that is a string, floating-point number, boolean, null, array, or object, **When** submitted, **Then** the API returns HTTP `422` with error code `invalid_request`; numeric strings and booleans are not coerced to integers.
5. **Given** age below `18` or above `100`, horizon below `1` or above `80`, or risk tolerance below `1` or above `10`, **When** submitted, **Then** the API returns HTTP `422` with error code `invalid_request` and does not return an allocation.

### User Story 3 - Understand the rule's scope (Priority: P2)

As a client or end user, I want the API's rule-based nature and limitations to be clear, so that I do not mistake a deterministic calculation for a guarantee or personalized financial advice.

**Independent Test**: Review the API documentation and any user-facing description; verify that both describe the calculation as a rule-based estimate and do not claim a guaranteed outcome.

**Acceptance Scenarios**:

1. **Given** the API documentation is published, **When** a user reads the allocation description, **Then** it identifies the result as a rule-based estimate and states that it is not individualized financial advice or a guarantee of returns.
2. **Given** any request, **When** the API computes its response, **Then** it uses only the submitted values and the documented formula, without randomness, external market data, hidden state, or machine-learning inference.

## Requirements

### Functional Requirements

- **FR-001**: The API MUST provide `POST /allocation` accepting a JSON object with exactly three required keys: `age`, `horizon_years`, and `risk_tolerance`.
- **FR-002**: Each of the three values MUST be a JSON integer. Boolean values MUST be rejected even in runtimes where booleans are integer subtypes. No implicit coercion or defaulting is permitted.
- **FR-003**: `age` MUST be in the inclusive range `18–100`; `horizon_years` MUST be in the inclusive range `1–80`; `risk_tolerance` MUST be in the inclusive range `1–10`.
- **FR-004**: The API MUST calculate the unrounded equity value as `100 - age + 4 * (risk_tolerance - 5) + 2 * (horizon_years - 10)`, clamp it to the inclusive range `0–100`, and round to the nearest whole percentage point, with exact half-point ties rounded up.
- **FR-005**: The fixed-income percentage MUST equal `100 - equities_percent`.
- **FR-006**: On success, the API MUST return HTTP `200`, JSON content type, and exactly this response shape with integer values: `{"equities_percent": <integer>, "fixed_income_percent": <integer>}`.
- **FR-007**: Malformed JSON MUST return HTTP `400` and exactly `{"error":{"code":"invalid_json","message":"Request body must be valid JSON."}}`.
- **FR-008**: Valid JSON that is not an object, or an object with missing, extra, wrongly typed, or out-of-range values, MUST return HTTP `422` with JSON content type and an error object whose code is `invalid_request`. Invalid requests MUST NOT return an allocation.
- **FR-009**: Error message text for `invalid_request` MAY describe the specific validation error, but MUST be non-empty and stable for the same validation failure. Error responses MUST use the shape `{"error":{"code":"invalid_request","message":"<non-empty message>"}}`.
- **FR-010**: The result MUST be deterministic: identical valid input under the same rule version MUST produce an identical response, without external data, randomness, hidden state, or model inference.
- **FR-011**: Documentation MUST state the exact formula, input bounds, rounding and clamping behavior, and that results are rule-based estimates, not individualized financial advice or guarantees of return.
- **FR-012**: The API MUST accept only `Content-Type: application/json`, optionally with `charset=utf-8` (case-insensitive). Missing, unsupported, or non-UTF-8 content types MUST return HTTP `415` with `{"error":{"code":"unsupported_media_type","message":"Content-Type must be application/json with UTF-8 encoding."}}`.
- **FR-013**: The API MUST accept only an absent `Content-Encoding` or `identity`. Other content encodings MUST return HTTP `415` with `{"error":{"code":"unsupported_media_type","message":"Content-Encoding must be absent or identity."}}`.
- **FR-014**: The API MUST limit request bodies to `16384` bytes. Larger bodies MUST return HTTP `413` with `{"error":{"code":"request_too_large","message":"Request body must not exceed 16384 bytes."}}`.
- **FR-015**: JSON with duplicate object keys MUST return HTTP `422` with error code `invalid_request`; the message MUST identify the duplicated key. Non-standard JSON constants such as `NaN` and `Infinity`, invalid UTF-8, and malformed JSON MUST be treated as malformed JSON under FR-007.
- **FR-016**: Age and horizon MUST be validated independently against their stated bounds; no additional age/horizon relationship is imposed.
- **FR-017**: When multiple request validation failures exist, the API MUST report one stable error using this order: missing fields in `age`, `horizon_years`, `risk_tolerance` order; then unexpected fields in lexicographic order; then type and range checks in `age`, `horizon_years`, `risk_tolerance` order. Only the first applicable failure is returned.
- **FR-018**: Determinism means semantic JSON equality, not byte-for-byte serialization equality. Rule versioning is internal; no rule-version field or versioned route is exposed. The route is `POST /allocation`.

### Key Entities

- **Allocation Request**: An object containing `age` (integer, `18–100`), `horizon_years` (integer, `1–80`), and `risk_tolerance` (integer, `1–10`).
- **Allocation Response**: An object containing `equities_percent` and `fixed_income_percent`, both integer percentages in `0–100` whose sum is `100`.
- **API Error**: An object containing an `error` object with a stable machine-readable `code` and human-readable `message`.

## Edge Cases

- The raw equity value may be below `0` or above `100`; clamp it before rounding.
- Exact half-point values MUST round upward (for example, `50.5` becomes `51`). With the current integer-only inputs and integer coefficients, the formula yields an integer, so no valid current request produces a half-point tie.
- Boundary inputs `age=18`, `age=100`, `horizon_years=1`, `horizon_years=80`, `risk_tolerance=1`, and `risk_tolerance=10` are valid.
- Empty body, invalid encoding, and malformed JSON are invalid JSON requests and MUST NOT result in a successful allocation.
- JSON `true` and `false` are invalid for all three fields, despite Python's `bool` subclassing `int`.
- Unknown request keys MUST be rejected rather than ignored.
- Duplicate keys anywhere in a JSON object MUST be rejected rather than resolved by occurrence order.
- A request with an age/horizon combination within both individual ranges is valid, including age `100` with horizon `80`.
- Missing/unsupported content type, unsupported content encoding, and oversized request bodies MUST use the explicit `415` and `413` contracts in FR-012–FR-014.
- Validation MUST report a single failure in the stable order defined by FR-017.

## Assumptions

- The transport is HTTP with a JSON request and response.
- Portfolio classes are limited to equities and fixed income; no additional asset class is implied.
- The formula and bounds above define a deterministic software rule only; they are not represented as a recommended or suitable investment strategy.
- The API does not require authentication, persistence, market data, or user-specific state for this feature.

## Out of Scope

- Selecting or optimizing the allocation formula based on investment research.
- Recommending particular securities, funds, or products.
- Forecasting performance, risk, or returns.
- Rebalancing, tax treatment, account management, or storing personal financial data.
