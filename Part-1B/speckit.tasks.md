# Implementation Tasks: AI Financial Persona Extractor

**Feature specification**: `speckit.specify.md`  
**Architecture and plan**: `speckit.plan.md`  
**Clarification review**: `speckit.clarify.md`  
**Constitution**: `speckit.constitution.md`

Tasks are dependency ordered. Part-1B is a separate application; do not copy Part-1A implementation or tests. Do not send biographies to an external provider until privacy, provider, and deployment decisions are approved.

## Phase 1 - Resolve Product and Data-Handling Decisions

- [ ] **T001 - Finalize horizon interpretation**
  - Decide which expressions support `investment_horizon_years`: whole-year statements, months, approximate durations, ranges, retirement ages, and other indirect expressions.
  - Define conversion/rounding rules if normalization is allowed; otherwise specify which expressions require clarification.
  - Update the spec with testable examples.
  - **Done when**: Every supported and unsupported horizon form has an explicit expected result.

- [ ] **T002 - Finalize risk evidence and precedence**
  - Specify when explicit numerical scores take precedence over qualitative evidence and when conflicts require clarification.
  - Decide handling for out-of-range explicit scores when qualitative evidence is also present.
  - Define the minimum subject-attributed evidence needed to select a rubric band, including treatment of quoted, negated, hypothetical, third-party, and mixed signals.
  - Confirm rubric phrases are contextual examples, not keyword triggers.
  - **Done when**: Each combination of valid/invalid numeric evidence and qualitative evidence maps to a score or clarification with no precedence ambiguity.

- [ ] **T003 - Define qualitative-score evaluation labels**
  - Establish an independent annotation protocol for selecting labeled reference scores within each risk band.
  - Define exact-match and band-accuracy calculations and how permitted non-deterministic within-band output is evaluated.
  - Preserve the constitution's `95%` per-field exact-match threshold and zero-guess clarification requirement.
  - Define repeated-run stability metrics for risk estimates.
  - **Done when**: Annotators and evaluators can assign labels and calculate each required metric consistently.

- [ ] **T004 - Define result and operational error boundary**
  - Specify the operational error schema/status for invalid input, malformed model output, missing provider configuration, timeout, rate limit, and provider/service failure.
  - Ensure operational errors cannot be represented as a successful extraction or as user clarification.
  - **Done when**: Each operational failure class has explicit handling separate from the five-key extraction result.

- [ ] **T005 - Finalize numeric bounds and input validation**
  - Decide whether to impose semantic upper bounds on age/horizon or only documented representation and input-size limits.
  - Define empty/whitespace biography behavior, malformed UTF-8/non-text behavior, and maximum input size.
  - Define whether invalid inputs produce a transport error or an extraction clarification.
  - **Done when**: All input classes and numeric limits have observable, testable behavior; no value is silently clamped.

- [ ] **T006 - Define target subject and clarification contract**
  - Specify behavior when a biography includes multiple people or the target person is unclear.
  - Decide whether exactly one question is required per unresolved field, whether a question may cover multiple fields, and stable ordering.
  - Decide whether clarification questions include machine-readable field identifiers; amend the exact output schema if so.
  - **Done when**: Multi-person handling, question count/order, and field-to-question mapping are unambiguous and acceptance-testable.

- [ ] **T007 - Approve execution and data-processing boundary**
  - Select library, CLI, HTTP API, or other transport.
  - Before selecting or calling an external model, approve provider, deployment region, privacy/data-processing terms, retention, cost/latency limits, timeout/retry behavior, and credential management.
  - Update the spec and plan with the approved choices.
  - **Done when**: Runtime and provider requirements are approved, or external provider calls are explicitly deferred.

## Phase 2 - Establish the Independent Part-1B Project

- [ ] **T008 - Scaffold the Part-1B Python package**
  - Create a new `src/financial_persona_extractor/` package, tests layout, and project configuration in Part-1B.
  - Do not reuse Part-1A application code or tests.
  - Add only dependencies needed for the approved runtime, validation, model adapter, and tests.
  - **Depends on**: T004, T005, T007.
  - **Done when**: The Part-1B package imports independently and its configured test runner discovers the Part-1B tests.

- [ ] **T009 - Define typed public and internal schemas**
  - Define biography input, extraction evidence/state, public output result, and operational error types.
  - Enforce the exact public top-level keys, nullable field behavior, strict integer checks (including rejecting booleans), and the `complete`/`clarification_required` invariants.
  - Add a schema version internally only if specified; never expose undocumented metadata.
  - **Depends on**: T004, T005, T006, T008.
  - **Done when**: Valid complete and clarification examples serialize to the exact approved schema, and invalid structures fail validation explicitly.

## Phase 3 - Implement Extraction Policy and Local Test Adapter

- [ ] **T010 - Implement age and horizon policy**
  - Accept age only when explicitly stated in years; never derive it from a birth date or birth year.
  - Apply only the horizon normalization rules finalized in T001.
  - Mark missing, conflicting, ambiguous, invalid, or out-of-bound values unresolved without guessing.
  - **Depends on**: T001, T005, T006, T009.
  - **Done when**: Each approved age/horizon example yields the specified value or a field-specific clarification.

- [ ] **T011 - Implement contextual risk rubric policy**
  - Map subject-attributed conservative, moderate, and aggressive qualitative evidence into the approved score bands `1–3`, `4–6`, and `7–10`.
  - Apply explicit-score precedence and invalid/conflicting evidence rules from T002.
  - Ignore unrelated, quoted, hypothetical, negated, or third-party phrases as subject preferences.
  - Return unresolved risk and a targeted question when evidence is absent or conflicting.
  - **Depends on**: T002, T006, T009.
  - **Done when**: Policy cases have the expected band or clarification and do not rely on literal keyword matching alone.

- [ ] **T012 - Implement clarification resolution and output validation**
  - Combine field-level results, set unresolved fields to `null`, and generate questions in the approved order and structure.
  - Enforce status/null/question consistency and exact response keys immediately before serialization.
  - **Depends on**: T009, T010, T011.
  - **Done when**: Every composed result satisfies all structural invariants, including multiple unresolved fields.

- [ ] **T013 - Define model-adapter interface and fake adapter**
  - Add a provider-neutral interface for structured extraction output.
  - Implement a deterministic fake adapter for tests only; make it possible to inject malformed output and operational failures.
  - Do not include an external provider SDK in this task.
  - **Depends on**: T008, T009.
  - **Done when**: Orchestration can be exercised offline with valid, invalid, incomplete, and failure responses.

- [ ] **T014 - Implement extraction orchestration**
  - Pass biography text to the injected model adapter under instructions that treat biography content as untrusted data.
  - Validate model output through the policy and schema layers; never repair missing values by guessing.
  - Map parsing/model/provider failures to the approved operational error path.
  - **Depends on**: T010, T011, T012, T013, T004.
  - **Done when**: End-to-end fake-adapter tests cover complete extraction, clarification, malformed model output, and operational errors.

## Phase 4 - Add Approved Runtime Integration

- [ ] **T015 - Implement the selected model-provider adapter**
  - Add the provider SDK and configuration only after T007 approval.
  - Request structured output where available, use bounded timeouts/retries, and surface provider errors explicitly.
  - Keep credentials out of source, fixtures, logs, and responses; do not log biographies or raw model output.
  - **Depends on**: T007, T013, T014.
  - **Done when**: Adapter contract tests pass and a controlled integration check succeeds without exposing personal data or secrets.
  - **Blocked until**: Provider and privacy/data-processing approval is recorded.

- [ ] **T016 - Implement the selected CLI/API transport**
  - Add the approved transport as a thin adapter around the extraction service.
  - Enforce the input encoding, size, and error behavior from T004/T005.
  - Return only the approved extraction schema for extraction/clarification results; use the approved operational error format otherwise.
  - **Depends on**: T004, T005, T007, T012, T014.
  - **Done when**: Transport contract tests verify request handling, success/clarification output, and operational error separation.

## Phase 5 - Test, Evaluate, Document, and Release

- [ ] **T017 - Add unit and invariant tests**
  - Cover exact schema keys, strict JSON/Python types, numeric domains, status invariants, partial results, and question mapping/order.
  - Cover explicit age and birth-date-only abstention; approved horizon forms; risk-band cases, precedence, no-evidence abstention, context attribution, and prompt-injection-style biography content.
  - **Depends on**: T009, T010, T011, T012.
  - **Done when**: All deterministic policy and schema invariants have automated coverage.

- [ ] **T018 - Add adapter and transport contract tests**
  - Cover valid model output, missing/extra/wrongly typed fields, out-of-range scores, malformed outputs, timeouts, rate limits, and provider failures.
  - Verify errors never appear as complete or clarification-required extraction results.
  - Test the selected transport's input constraints and output/error envelopes.
  - **Depends on**: T013, T014, T016.
  - **Done when**: All adapter and transport behaviors meet the finalized contract without live provider dependence in routine tests.

- [ ] **T019 - Build the held-out evaluation harness**
  - Create approved, independently labeled clear, ambiguous, conflicting, and unsupported cases using synthetic or de-identified data.
  - Keep tuning and held-out examples separate and version the dataset/annotation instructions.
  - Report per-field exact-match accuracy, qualitative risk band accuracy, repeated-run stability, and clarification-suite unsupported-value count.
  - **Depends on**: T003, T010, T011, T014.
  - **Done when**: Evaluation is reproducible and reports every constitutional threshold independently.

- [ ] **T020 - Document the feature and operational limitations**
  - Document input, exact output/error contracts, age/horizon interpretation, risk rubric/precedence, clarification behavior, privacy/provider handling, and financial-scope disclaimer.
  - Document setup, run/test/evaluation commands and the approved provider configuration without embedding credentials.
  - **Depends on**: T001–T019 as applicable.
  - **Done when**: Documentation matches the implemented and approved contract and explains all non-deterministic behavior and limitations.

- [ ] **T021 - Run quality, safety, and privacy gates**
  - Run the full Part-1B test suite, configured lint/type/security checks, and evaluation harness.
  - Verify no biography text, prompts, model output, credentials, or personal extracted values are logged or committed unintentionally.
  - Verify no unapproved external calls, persistence, provider fallback, or financial recommendations are present.
  - **Depends on**: T017, T018, T019, T020.
  - **Done when**: All checks pass, every constitution threshold is met, and failures/environment limitations are reported explicitly.

- [ ] **T022 - Perform release-readiness review**
  - Review schema compatibility, unresolved operational risks, privacy controls, provider approvals, evaluation results, and rollback/versioning plan.
  - **Depends on**: T021.
  - **Done when**: Release is explicitly approved or remaining blockers are documented; no blocked provider integration is represented as production-ready.
