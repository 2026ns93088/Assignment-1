# AI Financial Persona Extractor Constitution

## Mission and Scope

The system extracts a limited set of financial-persona facts from unstructured natural-language biographies. It is an information-extraction tool, not a financial adviser, risk profiler, or portfolio recommender. It MUST NOT turn extracted information into investment advice or recommendations.

The required fields are:

- `age`: positive integer.
- `investment_horizon_years`: positive integer.
- `risk_tolerance_score`: integer from `1` through `10`, inclusive.

## Core Principles

### 1. Output Schema Contract

Every feature specification MUST define a machine-readable output schema before implementation. At minimum, the schema MUST:

- Use the exact field names `age`, `investment_horizon_years`, and `risk_tolerance_score`.
- Define each field's type and inclusive domain constraints as specified above.
- Define how unavailable, ambiguous, invalid, and successfully extracted values are represented, including whether the response carries a status and clarification question.
- Define whether additional fields are allowed. Implementations MUST NOT add undocumented output fields.
- Be structurally valid and consistently serialized on every response, including responses that request clarification.

Unresolved fields MUST NOT be represented using fabricated numeric values, zero, or any other value that could be mistaken for an extraction. A specification MUST make unresolved-field representation explicit and MUST distinguish a complete extraction from a request for clarification.

### 2. Structural Invariants

- Every non-null `age` and `investment_horizon_years` MUST be an integer greater than zero; every non-null `risk_tolerance_score` MUST be an integer in `1–10`.
- The extractor MUST NOT coerce strings, floating-point values, booleans, or out-of-range values into valid numbers.
- A response MUST conform to its declared schema. Field names, types, and status semantics MUST NOT vary based on model wording or sampling.
- A value MUST NOT be emitted as extracted unless it is supported by the biography or by a derivation rule explicitly defined in the feature specification.
- Any derivation (for example, calculating age from a birth date) MUST specify its reference date, formula, and boundary behavior. Otherwise the system MUST request clarification rather than derive it.

### 3. Behavioural Properties

- The system MAY use a non-deterministic AI model; identical inputs are not required to produce byte-identical or semantically identical outputs.
- Non-determinism MUST NOT relax schema validity, numeric constraints, evidence requirements, abstention behavior, or safety rules.
- The system MUST extract only the three in-scope fields. It MUST ignore unrelated biography details and MUST NOT infer financial facts from stereotypes, demographic proxies, writing style, or unstated assumptions.
- A `risk_tolerance_score` MUST be directly supported by an explicit score or by a documented, validated mapping rubric. Qualitative descriptions MUST NOT be assigned a numeric score without such a rubric.
- When one or more mandatory values are absent, ambiguous, contradictory, or unsupported, the system MUST request clarification for those values and MUST NOT guess them. Clearly supported fields MAY be returned alongside unresolved fields only if the output schema explicitly defines that partial-result behavior.
- If sources conflict, the system MUST identify the conflict and request clarification unless a precedence rule is explicitly defined and validated.

### 4. Safety and Guardrail Rules

- The extractor MUST describe its output as information found or derived under documented rules, not as verified truth or a financial recommendation.
- The extractor MUST NOT fabricate, silently resolve, or overstate certainty about personal or financial information.
- Biographies and extracted financial-persona values MUST be treated as sensitive personal data. Implementations MUST minimize collection, retention, logging, and disclosure; any storage or secondary use requires an explicit specification and appropriate safeguards.
- Untrusted biography text MUST be treated only as data to analyze, never as instructions to override system behavior, schema, privacy rules, or safety constraints.
- Errors, unsupported input, and model/service failures MUST NOT be converted into success-shaped outputs or guessed values. Failure behavior MUST be explicit in the feature specification.

### 5. Evaluation Threshold

Before release, the implementation MUST be evaluated on a fixed, independently labeled dataset that is separated from prompt development and tuning:

- For each of the three fields, exact-match accuracy MUST be at least `95%` on held-out examples where that field is clearly stated or derivable under the documented rules.
- On the missing, ambiguous, contradictory, and unsupported-information evaluation suite, the number of guessed or unsupported extracted values MUST be `0`. Cases requiring clarification MUST request clarification rather than emit a numeric guess.
- Results MUST be reported per field and for the clarification suite. A combined average MUST NOT hide a field or safety-suite failure.
- Evaluation data, labeling rules, scoring method, and thresholds MUST be documented and reproducible. Changes to prompts, models, mappings, or schema MUST trigger reevaluation.

## Governance

This constitution governs all Part-1B specifications and implementations. A feature specification MUST define its output schema, structural invariants, behavioural properties, safety/guardrail rules, and evaluation method in a way that satisfies these principles. Where implementation details are not defined, the system MUST abstain and request clarification rather than invent policy or data.

Changes to field semantics, mapping rubrics, output schema, model behavior, or evaluation thresholds require documented rationale, updated tests and evaluation results, and review for compatibility and privacy impact.

**Version**: 1.0.0  
**Ratified**: 2026-11-05  
**Last Amended**: 2026-11-05
