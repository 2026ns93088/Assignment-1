# Asset Allocation API Constitution

## Core Principles

### 1. Deterministic, Explainable Allocation
Allocation decisions MUST come only from explicit, documented mathematical rules. The same valid input and rule version MUST always produce the same response. Implementations MUST NOT use randomness, external market data, hidden state, or machine-learning inference to determine an allocation. Every adjustment to a baseline rule (including age- and risk-based adjustments) MUST be documented and covered by tests.

### 2. Strict Input and Output Contracts
The API MUST accept and return JSON that conforms to a documented schema. Age, investment horizon, and risk tolerance MUST be integers; risk tolerance MUST be in the inclusive range 1–10. Implementations MUST reject malformed JSON, missing or unexpected fields, wrong types, and values outside documented domain limits rather than silently coercing or defaulting them. In Python, booleans MUST NOT be accepted as integers. Successful responses MUST use a stable, documented shape and valid portfolio percentages that sum to 100.

### 3. Financial Safety and Clear Scope
The API MUST present allocations as rule-based estimates, not guaranteed returns or individualized financial advice. It MUST NOT imply that an allocation ensures a particular outcome. Any assumptions and material limitations of the allocation rules MUST be documented and communicated consistently.

### 4. Verifiable Correctness
Every allocation rule and input boundary MUST have automated tests, including representative cases, boundaries, invalid inputs, and percentage-sum invariants. Tests MUST verify the specified output and deterministic behavior, not merely that the API responds. Rule changes MUST update the documentation and tests in the same change.

### 5. Small, Maintainable Python API
The implementation MUST keep request validation, allocation calculations, and HTTP or command-line transport concerns clearly separated. Core calculations MUST be independently testable and free of I/O. Dependencies MUST be kept minimal and justified; public behavior and errors MUST be documented.

## Governance

This constitution takes precedence over conflicting project conventions. Changes to allocation behavior require an explicit rule rationale, updated documentation, and regression tests. Amendments MUST be reviewed alongside their impact on API compatibility and existing allocations.

**Version**: 1.0.0  
**Ratified**: 2026-11-05  
**Last Amended**: 2026-11-05
