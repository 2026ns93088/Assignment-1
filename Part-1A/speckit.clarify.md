# Specification Clarification Review

**Reviewed**: `spec.md` against `constitution.md`  
**Scope**: Identify unresolved behavior and edge cases; the approved allocation formula and bounds are not changed.

## Findings

### High priority

1. **Age and horizon relationship is unspecified.** The current independent bounds allow requests such as age `100` with an `80`-year horizon. Is that valid because the API treats horizon as an independent formula input, or should horizon be capped by age, expected lifespan, or another rule? The spec should explicitly state the intended relationship; avoid inferring a financial or lifespan assumption.

2. **Duplicate JSON object keys are ambiguous.** A body such as `{"age":40,"age":70,"horizon_years":10,"risk_tolerance":5}` may be accepted with either age depending on the parser. Should duplicate keys be rejected as `invalid_request` (recommended for strict input), or should a specific occurrence win?

3. **Transport-level input requirements are incomplete.** The spec does not define behavior for a missing or non-JSON `Content-Type`, unsupported content encodings, or an oversized request body. Should the API require `application/json`, reject unsupported media types with `415`, and enforce a documented body-size limit? Invalid byte encoding is listed as invalid JSON, but its exact error status and body should be confirmed.

### Medium priority

4. **Route and error conventions were selected in the draft, not established by the original feature request.** The spec defines `POST /allocation`, `400` for malformed JSON, and `422` for valid-but-invalid requests. Confirm these are the intended public API contract, including whether the endpoint needs a version prefix.

5. **Multiple simultaneous validation failures have no precedence rule.** FR-009 requires a stable message for the same failure, but does not say whether the API returns one error or all errors, nor which field is reported first when several are invalid. Define deterministic validation/error ordering or specify an ordered list of validation errors.

6. **Strict JSON number interpretation is not fully spelled out.** The spec rejects floating-point values, but does not explicitly address non-standard numeric tokens such as `NaN` and `Infinity`, which some Python JSON parsers accept as extensions. Clarify that only standards-compliant JSON is accepted and such tokens are rejected as `invalid_json`, if strict parsing is intended.

7. **Rounding is specified but cannot occur for the current inputs.** Integer inputs and integer coefficients make the raw formula an integer for every valid request. The half-up rule is therefore untestable and has no current effect. Keep it as a forward-compatibility rule, or remove it until fractional adjustments are introduced.

### Low priority

8. **Determinism is defined at the response-body level, but not for error serialization.** If byte-for-byte response determinism is required, clarify whether JSON key ordering and whitespace are part of the contract. Otherwise, state that determinism is semantic JSON equality, not identical serialization bytes.

9. **Rule-version handling is not defined.** FR-010 refers to identical results “under the same rule version,” but neither a version field nor versioned route is specified. Clarify whether rule versioning is only a development/release concept or must be exposed to API clients.

## Suggested Clarifications

- Decide whether horizon is independent of age or subject to an additional relationship constraint.
- Define duplicate-key handling and require standards-compliant JSON parsing.
- Define media-type, invalid-encoding, and request-size behavior if this API is exposed over HTTP.
- Confirm the endpoint path and selected HTTP status conventions before treating them as compatibility commitments.
- Specify stable validation ordering and whether errors are returned singly or collectively.
- Decide whether rounding and API-visible rule versioning are intentional requirements now or future-facing language.
