# Part 1B Harness Log

## Evaluation Configuration
* **Model:** Mock LLM Adapter (scripted fixtures; no model or network call).
* **Evaluation mode:** MOCK fixtures; smoke test only, not model accuracy.
* **Dataset:** 15 cases from `evals/dataset.json`.
* **Evaluation thresholds:** 100% structural validity and risk-band accuracy; at least 95% exact match for each scored field; zero unsupported guesses. No 80% aggregate threshold is configured.
* **Scoring method:** Layer 1 checks response structure; Layer 2 checks invariants, age/horizon matches, and clarification behavior; Layer 3 checks risk exact-match, rubric band, and abstention.
* **Run time (UTC):** 2026-11-05T08:14:09.687093+00:00

## Harness Execution 1 (Failure)
* **Outcome:** FAIL (initial run before the mock adapter was added).
* **Evidence:** The semantic evaluator returned `adapter_not_configured`; all three evaluation layers were `NOT_RUN`, and the CLI returned aggregate `FAIL`.

## Repair Cycle
* **Feedback:** Implement a mock adapter so all 15 cases can exercise the evaluation layers without API credentials or network access.
* **Repair:** Added a scripted fixture adapter keyed to the dataset biographies. It simulates expected outputs and is for harness verification only, not a live model or accuracy test.

## Re-evaluation
* **Outcome:** PASS
* **Evidence:** The latest pipeline output, including per-layer metrics and checks, is recorded below.

## LINT_GUARD

Command: `ruff check src .harness`

Status: **PASSED**

```text
All checks passed!
```

## SECURITY_SAST_GUARD

Command: `bandit -r src .harness/mock_adapter.py`

Status: **PASSED**

```text
Run started:2026-11-05 08:14:09.530681+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 830
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
Files skipped (0):
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.7
```

## AI_SEMANTIC_EVALUATOR

Command: `C:\Users\Saurav\AppData\Local\Programs\Python\Python313\python.exe -m financial_persona_extractor.evaluation --adapter mock_adapter:create_adapter`

Status: **PASSED**

```text
{
  "decision": "PASS",
  "thresholds": {
    "structural_validity": 1.0,
    "age_exact_match": 0.95,
    "horizon_exact_match": 0.95,
    "risk_exact_match": 0.95,
    "risk_band_accuracy": 1.0,
    "unsupported_guesses": 0
  },
  "metrics": {
    "case_count": 15,
    "runs_per_case": 1,
    "total_runs": 15,
    "layer1_structural": {
      "passed": 15,
      "total": 15,
      "decision": "PASS"
    },
    "layer2_invariants": {
      "passed": 15,
      "total": 15,
      "age_exact_match": 1.0,
      "horizon_exact_match": 1.0,
      "case_results_all_checks_passed": 15,
      "decision": "PASS"
    },
    "layer3_risk_semantics": {
      "passed": 15,
      "total": 15,
      "risk_exact_match": 1.0,
      "risk_band_accuracy": 1.0,
      "exact_case_results_passed": 15,
      "unsupported_guess_count": 0,
      "repeated_band_consistency": null,
      "decision": "PASS"
    }
  },
  "cases": [
    {
      "id": 1,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 2,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 3,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 4,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 5,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 6,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 7,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 8,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 9,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 10,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 11,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 12,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 13,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 14,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    },
    {
      "id": 15,
      "layer1": "PASS",
      "layer2": "PASS",
      "layer3": "PASS",
      "issues": []
    }
  ]
}
```

## Final Human Review
* **Decision:** PENDING — requires a human reviewer; the harness does not issue human acceptance.
* **Limitations & residual risks:** Mock fixtures are fixed and mirror this dataset; a passing result verifies evaluator plumbing only and does not establish real-model accuracy, non-deterministic behavior, or generalization. Any live-provider evaluation requires separate approval and secure configuration.