# Assignment-1 User Guide

This repository contains two independent Python projects. Use Python 3.11+ and install dependencies separately in each part's directory.

> Neither project provides individualized financial advice or guarantees returns.

## Part-1A: Asset Allocation API

Deterministic FastAPI service. From the repository root:

```powershell
Set-Location .\Part-1A
python -m pip install -e ".[test]"
python -m uvicorn asset_allocation.app:app --reload
```

Send `POST /allocation` with JSON:

```json
{"age": 40, "horizon_years": 10, "risk_tolerance": 5}
```

The response is `{"equities_percent": 60, "fixed_income_percent": 40}`. Equities use `clamp(100 - age + 4*(risk_tolerance - 5) + 2*(horizon_years - 10), 0, 100)`; fixed income is the remainder. Inputs must be integers: age 18–100, horizon 1–80 years, risk 1–10. Invalid requests return JSON errors.

Run tests and the Ruff/Bandit/test harness from `Part-1A`:

```powershell
python -m pytest
python .harness/runner.py
```

## Part-1B: Financial Persona Extractor

Validates extraction results for age, investment horizon, and risk score. Missing or unsupported fields must be null and request clarification. No live model provider is configured.

From the repository root:

```powershell
Set-Location .\Part-1B
python -m pip install -e ".[test]"
python -m pytest
python .harness/eval_runner.py
```

The harness uses fixed mock responses for the 15-case dataset and writes `.harness/harness-log.md`. A mock `PASS` verifies the harness only; it does not demonstrate real-model accuracy. Use a live adapter only after provider and privacy approval:

```powershell
python .harness/eval_runner.py --adapter module:factory --repeats 5
```

See each part's README and `speckit.*.md` files for detailed contracts, limitations, and plans. Part-specific tests, evaluation data, and evidence are kept separate.
