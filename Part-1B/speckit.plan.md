# Technical Architecture and Implementation Plan

**Feature**: AI Financial Persona Extractor  
**Inputs**: `speckit.constitution.md`, `speckit.specify.md`, `speckit.clarify.md`  
**Status**: Proposed; contract questions in section 9 must be resolved before production behavior is frozen.

## 1. Goals and Constraints

Build a Python service that accepts one natural-language biography and emits only the specified financial-persona fields, status, and targeted clarification questions. The service may use a non-deterministic AI model to interpret qualitative risk language, but it MUST validate every model result against the output contract and refuse unsupported values.

Non-goals include portfolio allocation, financial advice, instrument selection, persistence, and deterministic reproduction of the model's exact qualitative score.

The implementation MUST:

- Keep biography processing isolated from transport and response serialization.
- Require explicit age in years; never calculate age from birth dates.
- Extract only an investment horizon supported by the biography and approved normalization rules.
- Use the approved qualitative risk bands only as semantic guidance, never as unconditional keyword matches.
- Return `null` and a targeted question for unresolved fields.
- Treat model output and biography content as untrusted input.
- Avoid sending personal biographies to an external provider until provider, privacy, retention, and deployment decisions are approved.

## 2. Proposed Architecture

### Request/response flow

1. **Transport adapter** accepts the biography as UTF-8 text and enforces the approved request/media/size limits once clarified.
2. **Input validator** rejects invalid transport data and distinguishes invalid input from an empty but valid biography.
3. **Extraction orchestrator** sends only the biography and the versioned extraction instructions to a configured model adapter. It does not expose credentials or provider details to domain code.
4. **Structured extraction adapter** parses the model's structured result into internal typed values and evidence classifications. The model response is untrusted; malformed or unexpected structures are not passed through.
5. **Evidence and policy validator** checks subject attribution, explicit-age requirements, horizon support, risk rubric band, conflicting evidence, and all policy decisions established by the finalized specification.
6. **Clarification resolver** sets unresolved fields to `null` and creates one targeted question for each unresolved field, in the specified order.
7. **Output validator/serializer** enforces the exact public schema and status invariants before returning JSON.
8. **Operational error handler** reports transport/provider/parsing failures separately from a successful extraction or a user clarification response.

### Component responsibilities

- **API/transport**: HTTP or other selected entry point, input decoding, request limits, status codes, and JSON response.
- **Domain contracts**: Python models/types for the fixed result schema and internal extraction state.
- **Model adapter**: provider-specific call, structured-output request, timeout and retry policy, and provider error translation.
- **Extraction policy**: age and horizon interpretation, risk evidence evaluation, precedence, and clarification rules.
- **Output validation**: exact keys, strict JSON integer semantics (including rejecting booleans), field bounds, valid status/null/question combinations.
- **Evaluation**: versioned labeled fixtures, deterministic structural and guardrail tests, and repeated-run semantic-risk metrics.

### Provider-neutral boundary

Define a narrow asynchronous or synchronous model-adapter interface so a provider can be selected later without changing extraction policy or the public schema. Do not select or call an external model until privacy/data-processing requirements, provider, credentials mechanism, cost/latency constraints, and deployment region are decided. Tests MUST use a local fake adapter and must not require network access or real personal biographies.

## 3. Output Contract

The public extraction response is exactly:

```json
{
  "status": "complete",
  "age": 34,
  "investment_horizon_years": 12,
  "risk_tolerance_score": 5,
  "clarification_questions": []
}
```

For unresolved information, preserve all keys and use `null` for unresolved field values. Use `status: "clarification_required"` and include a specific question for each null field. `complete` requires all three values to be non-null and no questions. No evidence, confidence, rationale, recommendation, or provider metadata is exposed unless the specification is explicitly amended.

Operational failures are not extraction results. The concrete transport/error envelope remains blocked by the clarification questions; never return a success or clarification-shaped result for a provider outage or malformed model response.

## 4. Proposed Python Project Layout

```text
Part-1B/
  src/
    financial_persona_extractor/
      __init__.py
      app.py                 # Entry point and API wiring
      api.py                 # Transport route and response mapping
      schemas.py             # Public and internal typed contracts
      extraction.py          # Orchestration and policy pipeline
      policy.py              # Evidence checks, field rules, clarification logic
      model_adapter.py       # Provider-neutral adapter interface
      errors.py              # Typed operational/domain failures
  tests/
    unit/
      test_policy.py
      test_schemas.py
    contract/
      test_api.py
    evaluation/
      test_extraction_evaluation.py
      fixtures/               # Synthetic or approved de-identified examples
  pyproject.toml
  README.md
```

Keep the existing `evidence/` folder reserved for explicitly labeled snapshots; do not overwrite or mix it with application source, generated biography data, credentials, or evaluation datasets without approval.

## 5. Technology Recommendations

- Python with static type annotations and a validation library or explicit validators that enforce exact types and schema invariants.
- A web framework is optional until the transport is confirmed; if HTTP is selected, keep it as a thin adapter around the extraction service.
- Use pytest for unit, contract, and evaluation tests.
- Use a provider SDK only after the provider and data-handling choices are approved. Pin supported dependency ranges and keep secrets in environment/secret-management facilities, never in source or logs.
- Use structured model output where supported, but always independently parse and validate it. Provider-side JSON mode is not a substitute for application validation.

## 6. Implementation Sequence

1. **Resolve contract blockers** from `speckit.clarify.md` and amend `speckit.specify.md`: horizon normalization, risk precedence, rubric annotations, error boundary, numeric/input limits, subject identity, question mapping/order, and repeat-run evaluation.
2. **Select the execution boundary**: CLI, library, HTTP API, or another interface; choose a model provider only after privacy and operational requirements are explicit.
3. **Create the minimal Python package** and test configuration under `Part-1B`; do not copy Part-1A code or tests because Part-1B is a different application.
4. **Define typed contracts** for biography input, extraction evidence/internal states, public result, and operational errors.
5. **Implement deterministic validation/policy code** for schema shape, non-null numeric domains, status invariants, targeted clarification, and all explicit-age and risk-band constraints.
6. **Implement a fake model adapter and orchestration** so policy and response behavior can be tested without provider access.
7. **Implement the selected real model adapter** with structured output, bounded timeouts/retries, privacy-safe configuration, and explicit error mapping.
8. **Add API/CLI transport** and connect input validation, orchestrator, output validation, and serialization.
9. **Build the evaluation harness** from independently annotated, approved data; separate tuning and held-out examples; report each field and the clarification suite separately.
10. **Document** the schema, interpretation and abstention policies, provider/data-handling choices, limitations, setup, run commands, and evaluation results.
11. **Run tests and quality gates**, including malformed model-output tests and prompt-injection-style untrusted biography content; do not treat embedded instructions as system directions.
12. **Review privacy and release readiness**: verify no biography content or secrets are logged, no unapproved external calls occur, and every constitution threshold is met.

## 7. Verification Strategy

### Unit and invariant tests

- Positive integer age/horizon and risk score `1–10` are accepted; booleans, floats, strings, arrays, objects, zero, negatives, and out-of-range values are rejected or mapped to clarification according to the finalized spec.
- `complete` iff all values are non-null and questions are empty.
- `clarification_required` iff at least one field is null and each null field has a corresponding specific question.
- Output has exactly the five documented keys; no additional fields or provider/model information.
- Explicit age is accepted; birth date/year alone never results in a derived age.
- Risk estimates always land in the assigned band; no-relevant-evidence cases abstain.
- Quoted, hypothetical, negated, third-party, and prompt-injection text does not become a subject preference or override policy.
- Horizon unit/range/approximation behavior is tested after the clarification decision is recorded.
- Conflicting numeric/qualitative risk evidence, invalid numeric scores, and multi-person biographies follow the finalized precedence/subject rules.

### Adapter and service tests

- Fake adapter tests cover valid structured output, missing fields, wrong types, extra keys, invalid score ranges, malformed model responses, timeouts, rate limits, and provider errors.
- Operational errors never become successful extraction or clarification results.
- Retries, if enabled, are bounded and do not duplicate or persist biography data.
- HTTP/CLI contract tests verify the selected transport's input constraints, status codes, error envelope, and output schema.

### Evaluation gates

- Each field achieves at least `95%` exact-match accuracy on its held-out clear/derivable set.
- Qualitative risk meets the rubric-band criterion and any approved exact-score annotation method.
- Missing/ambiguous/contradictory/unsupported suite has zero guessed or unsupported values and valid field-specific clarification.
- Report results per field and for the safety/clarification suite; no aggregate may conceal a failed threshold.
- Repeat-run risk evaluation follows the clarified stability rule and remains separate from exact-match accuracy.

## 8. Privacy and Operational Requirements

- Do not log full biographies, raw provider prompts/responses, or extracted personal values by default.
- Redact or omit sensitive content from errors and telemetry.
- Do not persist inputs/results unless an explicit retention purpose, duration, access control, and deletion policy are approved.
- Use synthetic or de-identified fixtures in tests and evaluation by default.
- Keep provider credentials out of repository files; fail explicitly if required configuration is absent.
- Do not silently fall back to another provider, a deterministic keyword extractor, a fabricated response, or cached personal data.

## 9. Contract Decisions Required Before Implementation

The current specification/clarification review leaves these observable behaviors unresolved. This plan intentionally does not choose them:

1. **Horizon normalization**: accept whole-year statements only, or normalize months/approximate expressions; define ranges and rounding.
2. **Risk precedence**: decide when a valid explicit score conflicts with qualitative statements, and how an out-of-range explicit score interacts with otherwise usable qualitative evidence.
3. **Risk evaluation labels**: define reference-score annotation and scoring for a non-deterministic within-band estimate while preserving constitution thresholds.
4. **Rubric evidence**: establish minimum subject-attributed evidence; confirm examples are contextual cues rather than keyword triggers.
5. **Operational failures**: define separate error schema/status and the distinction from a clarification result.
6. **Numeric limits**: set maximum age/horizon or a transport/representation bound without silently clamping values.
7. **Ambiguous expressions**: define acceptable verbal age/horizon expressions and which require clarification.
8. **Clarification structure**: choose one question per unresolved field or another rule, stable order, and whether machine-readable field identifiers are allowed in the output.
9. **Subject selection**: define handling for multiple people or an unclear target person.
10. **Input bounds**: define empty/whitespace input, UTF-8 failures, non-text requests, and maximum biography size.
11. **Repeated-run behavior**: decide whether risk stability is measured by band consistency only or stricter consistency.
12. **Runtime/provider**: choose transport and provider only after data privacy, jurisdiction, retention, cost, timeout, and credential requirements are known.

Implementation may begin on isolated typed contracts, schema validation, fake-adapter tests, and non-controversial policy checks. Provider integration, public API error semantics, and ambiguous-language behavior MUST wait for the applicable decisions.

## 10. Risks and Mitigations

- **Non-deterministic scores can make acceptance inconsistent**: validate bands and evidence on every run; define scoring annotations and report repeated-run behavior separately.
- **Keyword shortcuts can misclassify people**: require context, subject attribution, polarity, and preference evidence rather than literal token matching.
- **Model output can violate the contract**: independently validate and reject malformed output; never repair it by guessing.
- **Sensitive biography exposure**: block external provider integration until privacy and provider decisions are approved; minimize logs, retention, and test-data exposure.
- **Unresolved policy can create incompatible clients**: freeze the questions in section 9 before documenting a stable deployment/API contract.
