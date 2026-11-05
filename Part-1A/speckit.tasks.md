# Implementation Tasks: Deterministic Asset Allocation API

**Feature**: `speckit.spec.md`  
**Architecture**: `speckit.plan.md`  
**Clarification review**: `speckit.clarify.md`

Tasks are ordered by dependency. The contract decisions and allocation formula are recorded in the specification.

## Phase 1 - Freeze API Decisions

- [x] **T001 - Resolve API contract questions**
  - Review the open decisions in `speckit.clarify.md` and record decisions in the specification before implementation.
  - Decide: age/horizon relationship; duplicate JSON key handling; media type, encoding, and body-size behavior; endpoint/version path and status codes; validation error ordering; standards-compliant JSON handling; rounding rule relevance; response determinism semantics; and rule-version visibility.
  - **Done when**: Every decision affecting observable behavior is either answered in `speckit.spec.md` or explicitly deferred as out of scope. Recommendations in the plan are not treated as requirements without approval.

## Phase 2 - Establish the Python Project

- [x] **T002 - Scaffold the minimal Python package**
  **Depends on**: T001
  - Create the package and test layout from `speckit.plan.md`, adapting only as needed to existing repository or assignment conventions.
  - Add project metadata and the selected runtime/test dependencies; configure the test runner.
  - Add a documented local setup, test, and run command.
  - **Done when**: The application package imports, the test runner discovers a smoke test, and documented commands work from a clean environment.

## Phase 3 - Implement the Allocation Domain

- [x] **T003 - Implement the pure allocation function**
  **Depends on**: T002
  - Add a function that calculates equity as `clamp(100 - age + 4 * (risk_tolerance - 5) + 2 * (horizon_years - 10), 0, 100)`.
  - Calculate fixed income as `100 - equities`.
  - Keep the function free of HTTP, parsing, logging, persistence, and external dependencies.
  - **Done when**: It returns the documented pair of integer percentages and has no observable side effects.

- [x] **T004 - Add allocation unit tests**
  **Depends on**: T003
  - Test the baseline `(40, 10, 5) -> (60, 40)`.
  - Test risk adjustments `(40, 10, 1) -> (44, 56)` and `(40, 10, 10) -> (80, 20)`.
  - Test upper and lower clamping `(18, 80, 10) -> (100, 0)` and `(100, 1, 1) -> (0, 100)`.
  - Test percentage ranges, integer output, sum-to-100 invariant, and repeated-input determinism.
  - **Done when**: All examples pass and invariant tests cover a useful set of valid input combinations, including boundaries.

## Phase 4 - Validate Requests Strictly

- [x] **T005 - Implement request validation**
  **Depends on**: T001, T002
  - Require a JSON object with exactly `age`, `horizon_years`, and `risk_tolerance`.
  - Require exact integer values; reject booleans, strings, floats, nulls, arrays, and objects without coercion.
  - Enforce inclusive ranges: age `18–100`, horizon `1–80`, risk tolerance `1–10`.
  - Apply the resolved duplicate-key, strict-JSON, age/horizon relationship, and validation-precedence decisions.
  - **Done when**: Valid requests produce validated typed values; all invalid requests produce a deterministic validation failure without calling the allocation function.

- [x] **T006 - Add validation unit tests**
  **Depends on**: T005
  - Cover each lower and upper bound as valid and values immediately outside each bound as invalid.
  - Cover missing and extra fields, non-object JSON values, and every prohibited value type, including booleans.
  - Cover duplicate keys, non-standard constants, and simultaneous failures according to T001 decisions.
  - **Done when**: Tests demonstrate strict type/range behavior and stable error selection or aggregation.

## Phase 5 - Implement the HTTP Contract

- [x] **T007 - Create the HTTP application and allocation route**
  **Depends on**: T003, T005
  - Create the app and implement the confirmed allocation route.
  - Connect transport parsing, validation, the pure allocation function, and JSON response serialization.
  - Return HTTP `200` with exactly `equities_percent` and `fixed_income_percent` on success.
  - Apply the agreed content-type, encoding, and request-size behavior.
  - **Done when**: A valid request reaches the domain function once and returns the specified JSON response with JSON content type.

- [x] **T008 - Implement standardized HTTP error responses**
  **Depends on**: T001, T007
  - Map malformed JSON to HTTP `400` and the exact `invalid_json` message and envelope in FR-007.
  - Map valid-but-invalid requests to HTTP `422` and the `invalid_request` envelope.
  - Ensure errors never contain allocation fields and messages follow the agreed stable validation policy.
  - Add specific handling for any other transport errors decided in T001.
  - **Done when**: Every specified error class has the agreed status, JSON shape, code, and stable message behavior.

- [x] **T009 - Add HTTP contract tests**
  **Depends on**: T007, T008
  - Test successful status, content type, exact response keys, expected values, and sum-to-100 invariant.
  - Test malformed/empty JSON, non-object JSON, missing/extra fields, wrong types, booleans, and out-of-range values.
  - Test media type, encoding, request-size, duplicate-key, and error precedence decisions from T001.
  - Verify errors do not include an allocation and repeated valid requests have semantically identical results.
  - **Done when**: Contract tests cover every acceptance scenario and resolved transport edge case.

## Phase 6 - Document, Verify, and Deliver

- [x] **T010 - Document the API and its limitations**
  **Depends on**: T007, T008
  - Document endpoint and method, request and response schemas, field bounds, formula, clamping and rounding behavior, status codes, and error bodies.
  - Explain that results are deterministic rule-based estimates, not individualized financial advice or guaranteed returns.
  - Document setup, run, and test commands.
  - **Done when**: Documentation agrees with the implemented behavior and makes no unsupported financial claims.

- [x] **T011 - Run quality checks and review contract consistency**
  **Depends on**: T004, T006, T009, T010
  - Run the focused full test suite and configured formatter, linter, and type checker.
  - Confirm all acceptance scenarios are covered and the formula, bounds, and response contract match the specification.
  - Fix defects caused by this feature and rerun affected checks.
  - **Done when**: Checks pass, or any environment limitation is reported explicitly with exact failing command and reason.

- [x] **T012 - Verify local application operation**
  **Depends on**: T011
  - Start the API using its documented command and submit one successful request and representative invalid requests.
  - Confirm the process starts, responds on the documented local route, and returns the expected status and JSON bodies.
  - **Done when**: Smoke checks pass and any started local process is stopped after verification.
