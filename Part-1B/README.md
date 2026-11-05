# Financial Persona Extractor

Part-1B is an independent Python package for validating AI-generated financial-persona extractions and evaluating them against `evals/dataset.json`. It does not choose or call an external model provider. A provider adapter is intentionally required because provider and biography privacy decisions have not been approved.

The public extraction object has exactly these keys:

```json
{
  "status": "complete",
  "age": 34,
  "investment_horizon_years": 12,
  "risk_tolerance_score": 5,
  "clarification_questions": []
}
```

An adapter must return `null` for unresolved fields and provide a specific question for each unresolved field. The package validates exact keys, strict integer types and ranges, status/null consistency, and field-targeted questions. It never silently installs a deterministic keyword extractor or provider fallback.

## Install and test

From the `Part-1B` directory:

```powershell
python -m pip install -e ".[test]"
python -m pytest
```

## Evaluation harness

The harness reads the checked-in 15-case `evals/dataset.json` by default. Supply an approved adapter factory using the `module:factory` form:

```powershell
python .harness/eval_runner.py --adapter my_adapter:create_adapter
```

The runner adds the Part-1B source tree to the import path, so it can run directly from the `Part-1B` directory without installing the package.
When no adapter is supplied, the runner uses the scripted fixtures in `.harness/mock_adapter.py`. The fixtures are keyed to the 15 checked-in biographies and exist only to exercise the harness, including Layer 3, offline. A mock `PASS` is **not** evidence of model accuracy or release readiness. Use `--adapter module:factory` to evaluate an actual approved adapter.

Each run writes its job output and aggregate decision to `.harness/harness-log.md`, including the evaluation mode and failures. Options such as `--adapter` and `--repeats` can be passed through:

```powershell
python .harness/eval_runner.py --adapter my_adapter:create_adapter --repeats 5
```

The factory must return an object implementing:

```python
def extract(biography: str, instructions: str) -> Mapping[str, object]:
    ...
```

The adapter must not log biography text or return unvalidated data as trusted output. The lower-level evaluation CLI still requires an explicit adapter; the harness runner selects the clearly labeled mock fixture by default.

### Evaluation layers and release threshold

- **Layer 1 — Structural JSON validation**: 100% of responses must have exactly the required keys, valid status/type/domain values, and an array of non-empty clarification strings.
- **Layer 2 — Age, horizon, and clarification properties**: status and expected age/horizon must match each case, each unresolved field must have a targeted question, and no question may target an already-resolved field. Age and horizon exact-match accuracy must each be at least 95%; an expected-null age or horizon must never be guessed.
- **Layer 3 — Risk semantics**: risk exact-match accuracy must be at least 95%; every scored result must be in the expected conservative (`1–3`), moderate (`4–6`), or aggressive (`7–10`) band; expected-null cases must contain no guessed score.
- **Aggregate decision**: `PASS` only when Layer 1 and Layer 2 pass and Layer 3 meets all thresholds; otherwise `FAIL`. The JSON report includes per-layer decisions, metrics, and failed case IDs without echoing biography text.

To observe non-deterministic behavior, run multiple samples per case:

```powershell
python .harness/eval_runner.py --adapter my_adapter:create_adapter --repeats 5
```

Repeated risk-band consistency is reported as a diagnostic; its release threshold remains pending the specification clarification.
