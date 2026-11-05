# Specification Clarification Review

**Reviewed**: `speckit.specify.md` against `speckit.constitution.md`  
**Scope**: Identify unresolved contract, interpretation, safety, and evaluation decisions. No feature behavior is changed by this review.

## Findings

### High priority

1. **Investment horizon normalization is not defined.** The spec accepts a positive integer number of years, but biographies may use months (“18 months”), ranges (“10–15 years”), approximate durations (“about a decade”), or a retirement age rather than an investment duration. Should only an explicitly stated, whole-number duration in years be accepted, or may the extractor convert/calculate other expressions? Define rounding and ambiguity behavior if conversions are allowed. The spec currently says no age-derived default, but does not state whether other horizon derivations are permitted.

2. **Conflicting risk evidence has an unclear precedence rule.** Section 5 says a valid self-attributed numeric score takes precedence when quantitative and qualitative evidence coexist, but also says materially contradictory evidence requires clarification. For example, “my risk score is 3, but I want aggressive growth and accept major losses” may be treated either as score `3` or as unresolved. Specify which conflicts trigger clarification and whether an explicit score can ever take precedence over a contradictory stated preference.

3. **The qualitative rubric does not uniquely determine the score.** Each category defines a band, while the model may choose any integer in it. The evaluation section requires exact-match accuracy against one labeled target score but does not say how a single reference score is selected or how acceptable variation within a band is scored. Define the annotation protocol for qualitative examples and reconcile single-score exact match with permitted non-deterministic variation, while retaining the constitution's minimum thresholds.

4. **Risk examples can be mistaken for unconditional keyword rules.** Phrases such as “crypto,” “fixed income,” “guaranteed,” and “stock market volatility” are not inherently expressions of the subject's own risk preference; they could describe a product, another person, a hypothetical, or a rejected strategy. The spec adds attribution/context safeguards, but does not define the minimum evidence required to place a statement in a band. Clarify whether the examples are illustrative only and how mixed or weak evidence is handled.

5. **Failure behavior is explicitly deferred, but the schema is defined as universal.** The output section says every response must have the extraction schema, while the safety section says provider, parsing, and service failure behavior must be specified before implementation. Should operational failures use a separate error schema/status, or must they also conform to the extraction envelope without posing as successful extraction? Define this boundary before implementation.

### Medium priority

6. **Positive integer fields have no upper bounds or numeric representation limits.** “Positive integer” accepts implausibly large ages/horizons, and JSON/Python integer capacity differs from downstream systems. Should the API impose plausible domain limits or a documented maximum digit count? If there is no semantic maximum, specify a serialization/size limit and clarify that the extractor should not silently clamp values.

7. **Ambiguous time expressions need field-specific rules.** It is unclear whether “I am in my mid-thirties,” “invest until my child finishes college,” “retire in 20 years,” or “invest for the next decade or so” can support a value. Decide which expressions are sufficiently precise and which must trigger clarification. Age is explicitly years-only, but acceptable natural-language age forms are not enumerated.

8. **Clarification question ordering and duplication are unspecified.** When several fields are unresolved, can question order vary? May one question cover multiple fields? Is exactly one question required per field, or merely at least one? Defining stable field order (`age`, horizon, risk) and one targeted question per unresolved field would simplify clients and evaluation.

9. **Risk labels for partial/invalid values need stronger definition.** If the biography contains an explicit score outside `1–10` plus qualitative preferences, the spec says the invalid score requires clarification and also says contradictory explicit evidence requires clarification. Clarify whether a valid qualitative estimate can fill the field in the presence of an invalid numeric statement, or whether any invalid explicit score makes the field unresolved.

10. **Subject identity and multiple people are not fully specified.** The system is described as extracting the biography's subject, but does not say how to handle biographies mentioning a partner, family member, or several profiles without a clearly identified primary subject. Specify the target-person rule and require clarification when the subject cannot be identified.

### Low priority

11. **Input validity and size are not defined.** The input is UTF-8 text, but empty/whitespace-only text, malformed encoding, extremely long biographies, and non-text input have no specified outcomes. Define accepted input bounds and explicit invalid-input behavior, including whether these cases request clarification or return a non-extraction error.

12. **Qualitative risk scoring is allowed to be non-deterministic, but no stability expectation is set.** Exact score variation within a band is permitted, yet substantial score swings on the same evidence may be undesirable. Decide whether band consistency alone is sufficient or whether evaluation should measure repeated-run band consistency separately.

13. **The clarification response guarantees a question for each null field but not a mapping from question to field.** Clients must infer which question resolves which field. Consider whether to add a machine-readable field identifier per question; if so, update the exact schema and key constraints.

## Suggested Clarifications

- Define accepted horizon expressions and whether units other than whole years may be normalized.
- Reconcile explicit risk scores, contradictory qualitative evidence, and invalid explicit scores with one precedence rule.
- Specify qualitative-score annotation and evaluation so permitted within-band non-determinism can be measured consistently and the required per-field exact-match threshold remains meaningful.
- State that rubric phrases are examples rather than literal keyword triggers and define evidence sufficient to assign a band.
- Define operational error responses separately from extraction/clarification responses.
- Set safe representation limits for age/horizon and define behavior for values exceeding them; never clamp or fabricate a substitute.
- Define target-person handling, accepted ambiguity, clarification ordering/multiplicity, and biography input limits.
- Decide whether repeated-run risk-score evaluation measures only band consistency or a stricter score-level consistency criterion.
