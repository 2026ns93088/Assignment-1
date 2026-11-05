"""Three-layer evaluation harness for evals/dataset.json."""

import argparse
import importlib
import json
import math
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from financial_persona_extractor.errors import ExtractionError
from financial_persona_extractor.model_adapter import ModelAdapter
from financial_persona_extractor.policy import (
    question_addresses_field,
    validate_result_invariants,
)
from financial_persona_extractor.schemas import (
    ExtractionResult,
    ExtractionStatus,
    validate_structure,
)

DEFAULT_DATASET = Path(__file__).resolve().parents[2] / "evals" / "dataset.json"
EXPECTED_CASE_KEYS = {
    "id",
    "category",
    "input_text",
    "expected_status",
    "expected_age",
    "expected_horizon",
    "expected_risk",
}
EXACT_MATCH_THRESHOLD = 0.95
EXPECTED_CASE_COUNT = 15
RISK_BANDS = (
    (1, 3, "conservative"),
    (4, 6, "moderate"),
    (7, 10, "aggressive"),
)


@dataclass(frozen=True)
class EvaluationCase:
    case_id: int
    category: str
    input_text: str
    expected_status: ExtractionStatus
    expected_age: int | None
    expected_horizon: int | None
    expected_risk: int | None


@dataclass(frozen=True)
class CaseResult:
    case_id: int
    layer1_passed: bool
    layer2_passed: bool
    layer2_properties_passed: bool
    layer3_passed: bool
    layer3_band_passed: bool
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.case_id,
            "layer1": "PASS" if self.layer1_passed else "FAIL",
            "layer2": "PASS" if self.layer2_passed else "FAIL",
            "layer3": "PASS" if self.layer3_passed else "FAIL",
            "issues": list(self.issues),
        }


def _validate_expected_value(
    case_id: int,
    field_name: str,
    value: object,
    maximum: int | None = None,
) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 1:
        raise ValueError(
            f"case {case_id}: {field_name} must be a positive integer or null."
        )
    if maximum is not None and value > maximum:
        raise ValueError(
            f"case {case_id}: {field_name} must be between 1 and {maximum}."
        )
    return value


def load_dataset(path: Path = DEFAULT_DATASET) -> list[EvaluationCase]:
    """Load and validate the fixed 15-case gold dataset."""
    try:
        raw_cases = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Cannot load evaluation dataset: {error.__class__.__name__}."
        ) from error

    if not isinstance(raw_cases, list) or len(raw_cases) != EXPECTED_CASE_COUNT:
        raise ValueError(
            f"Evaluation dataset must contain exactly {EXPECTED_CASE_COUNT} cases."
        )

    cases: list[EvaluationCase] = []
    seen_ids: set[int] = set()
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict) or set(raw_case) != EXPECTED_CASE_KEYS:
            raise ValueError(
                "Each evaluation case must have exactly the documented keys."
            )

        case_id = raw_case["id"]
        if type(case_id) is not int or not 1 <= case_id <= EXPECTED_CASE_COUNT:
            raise ValueError("Evaluation case ids must be integers from 1 through 15.")
        if case_id in seen_ids:
            raise ValueError(f"Duplicate evaluation case id: {case_id}.")
        seen_ids.add(case_id)

        if (
            not isinstance(raw_case["category"], str)
            or not raw_case["category"].strip()
        ):
            raise ValueError(f"case {case_id}: category must be a non-empty string.")
        if not isinstance(raw_case["input_text"], str):
            raise TypeError(f"case {case_id}: input_text must be a string.")

        try:
            expected_status = ExtractionStatus(
                {
                    "SUCCESS": ExtractionStatus.COMPLETE.value,
                    "CLARIFICATION_REQUIRED": ExtractionStatus.CLARIFICATION_REQUIRED.value,
                }[raw_case["expected_status"]]
            )
        except (KeyError, TypeError) as error:
            raise ValueError(f"case {case_id}: invalid expected_status.") from error

        expected_age = _validate_expected_value(
            case_id,
            "expected_age",
            raw_case["expected_age"],
        )
        expected_horizon = _validate_expected_value(
            case_id,
            "expected_horizon",
            raw_case["expected_horizon"],
        )
        expected_risk = _validate_expected_value(
            case_id,
            "expected_risk",
            raw_case["expected_risk"],
            maximum=10,
        )
        if expected_status is ExtractionStatus.COMPLETE and any(
            value is None for value in (expected_age, expected_horizon, expected_risk)
        ):
            raise ValueError(f"case {case_id}: SUCCESS requires all expected fields.")
        if expected_status is ExtractionStatus.CLARIFICATION_REQUIRED and all(
            value is not None
            for value in (expected_age, expected_horizon, expected_risk)
        ):
            raise ValueError(
                f"case {case_id}: clarification requires an unresolved field."
            )

        cases.append(
            EvaluationCase(
                case_id=case_id,
                category=raw_case["category"],
                input_text=raw_case["input_text"],
                expected_status=expected_status,
                expected_age=expected_age,
                expected_horizon=expected_horizon,
                expected_risk=expected_risk,
            )
        )

    if seen_ids != set(range(1, EXPECTED_CASE_COUNT + 1)):
        raise ValueError("Evaluation case ids must be exactly 1 through 15.")
    return sorted(cases, key=lambda case: case.case_id)


def _expected_accuracy_threshold(total: int) -> int:
    return math.ceil(EXACT_MATCH_THRESHOLD * total)


def _risk_band(score: int) -> str:
    for minimum, maximum, band in RISK_BANDS:
        if minimum <= score <= maximum:
            return band
    raise ValueError(f"Risk score outside 1-10: {score}.")


def _check_questions(
    result: ExtractionResult,
    expected_unresolved: Mapping[str, bool],
) -> list[str]:
    issues: list[str] = []
    unresolved = [
        field for field, is_missing in expected_unresolved.items() if is_missing
    ]
    for field in unresolved:
        if not any(
            question_addresses_field(question, field)
            for question in result.clarification_questions
        ):
            issues.append(f"missing_targeted_question:{field}")

    for question in result.clarification_questions:
        targets = [
            field
            for field in expected_unresolved
            if question_addresses_field(question, field)
        ]
        if not targets or any(field not in unresolved for field in targets):
            issues.append("question_does_not_target_only_unresolved_fields")
    return issues


def _evaluate_single(
    case: EvaluationCase,
    adapter: ModelAdapter,
) -> tuple[CaseResult, ExtractionResult | None]:
    issues: list[str] = []
    try:
        candidate = adapter.extract(case.input_text)
        result = validate_structure(candidate)
    except ExtractionError as error:
        issue = f"extraction_error:{error.code}"
        return CaseResult(
            case.case_id,
            layer1_passed=False,
            layer2_passed=False,
            layer2_properties_passed=False,
            layer3_passed=False,
            layer3_band_passed=False,
            issues=(issue,),
        ), None

    layer1_passed = True
    layer2_property_issues: list[str] = []
    try:
        validate_result_invariants(result)
    except ExtractionError as error:
        layer2_property_issues.append(f"result_invariant:{error.code}")

    if result.status is not case.expected_status:
        layer2_property_issues.append("status_mismatch")
    layer2_value_issues: list[str] = []
    if result.age != case.expected_age:
        layer2_value_issues.append("age_mismatch")
    if result.investment_horizon_years != case.expected_horizon:
        layer2_value_issues.append("horizon_mismatch")

    expected_unresolved = {
        "age": case.expected_age is None,
        "investment_horizon_years": case.expected_horizon is None,
        "risk_tolerance_score": case.expected_risk is None,
    }
    if expected_unresolved["age"] and result.age is not None:
        layer2_property_issues.append("unsupported_age_guess")
    if (
        expected_unresolved["investment_horizon_years"]
        and result.investment_horizon_years is not None
    ):
        layer2_property_issues.append("unsupported_horizon_guess")
    layer2_property_issues.extend(_check_questions(result, expected_unresolved))

    layer3_issues: list[str] = []
    if result.risk_tolerance_score != case.expected_risk:
        layer3_issues.append("risk_exact_match_mismatch")
    layer3_band_passed = True
    if case.expected_risk is None:
        if result.risk_tolerance_score is not None:
            layer3_issues.append("unsupported_risk_guess")
            layer3_band_passed = False
    elif result.risk_tolerance_score is not None:
        expected_band = _risk_band(case.expected_risk)
        actual_band = _risk_band(result.risk_tolerance_score)
        if actual_band != expected_band:
            layer3_issues.append("risk_band_mismatch")
            layer3_band_passed = False
    else:
        layer3_band_passed = False

    issues.extend(layer2_property_issues)
    issues.extend(layer2_value_issues)
    issues.extend(layer3_issues)
    return (
        CaseResult(
            case.case_id,
            layer1_passed,
            not layer2_property_issues and not layer2_value_issues,
            not layer2_property_issues,
            not layer3_issues,
            layer3_band_passed,
            tuple(issues),
        ),
        result,
    )


def evaluate_cases(
    cases: Sequence[EvaluationCase],
    adapter: ModelAdapter,
    repeats: int = 1,
) -> dict[str, object]:
    """Evaluate every case and aggregate the three requested quality layers."""
    if type(repeats) is not int or repeats < 1:
        raise ValueError("repeats must be a positive integer.")
    if not cases:
        raise ValueError("At least one evaluation case is required.")

    case_results: list[CaseResult] = []
    total_runs = len(cases) * repeats
    exact_matches = {"age": 0, "horizon": 0, "risk": 0}
    scored_cases = {
        "age": sum(case.expected_age is not None for case in cases),
        "horizon": sum(case.expected_horizon is not None for case in cases),
        "risk": sum(case.expected_risk is not None for case in cases),
    }
    risk_band_matches = 0
    unsupported_guess_count = 0
    run_scores: dict[int, list[int | None]] = {}

    for case in cases:
        for _ in range(repeats):
            result_record, result = _evaluate_single(case, adapter)
            case_results.append(result_record)
            if result is None:
                continue
            if result.age == case.expected_age and case.expected_age is not None:
                exact_matches["age"] += 1
            if (
                result.investment_horizon_years == case.expected_horizon
                and case.expected_horizon is not None
            ):
                exact_matches["horizon"] += 1
            if (
                result.risk_tolerance_score == case.expected_risk
                and case.expected_risk is not None
            ):
                exact_matches["risk"] += 1
            if case.expected_risk is None:
                if result.risk_tolerance_score is not None:
                    unsupported_guess_count += 1
            elif result.risk_tolerance_score is not None and _risk_band(
                result.risk_tolerance_score
            ) == _risk_band(case.expected_risk):
                risk_band_matches += 1
            run_scores.setdefault(case.case_id, []).append(result.risk_tolerance_score)

    layer1_passed = sum(record.layer1_passed for record in case_results)
    layer2_passed = sum(record.layer2_passed for record in case_results)
    layer2_properties_passed = sum(
        record.layer2_properties_passed for record in case_results
    )
    layer3_passed = sum(record.layer3_passed for record in case_results)
    layer3_band_passed = sum(record.layer3_band_passed for record in case_results)

    accuracies = {
        field: (
            exact_matches[field] / (scored_cases[field] * repeats)
            if scored_cases[field]
            else 0.0
        )
        for field in ("age", "horizon", "risk")
    }
    layer1_ok = layer1_passed == total_runs
    layer2_ok = (
        layer2_properties_passed == total_runs
        and exact_matches["age"]
        >= _expected_accuracy_threshold(scored_cases["age"] * repeats)
        and exact_matches["horizon"]
        >= _expected_accuracy_threshold(scored_cases["horizon"] * repeats)
    )
    layer3_ok = (
        exact_matches["risk"]
        >= _expected_accuracy_threshold(scored_cases["risk"] * repeats)
        and layer3_band_passed == total_runs
        and risk_band_matches == scored_cases["risk"] * repeats
        and unsupported_guess_count == 0
    )
    repeated_band_consistency: float | None = None
    if repeats > 1:
        comparable_cases = [
            scores
            for scores in run_scores.values()
            if len(scores) == repeats and all(score is not None for score in scores)
        ]
        if comparable_cases:
            stable_cases = sum(
                len({_risk_band(score) for score in scores if score is not None}) == 1
                for scores in comparable_cases
            )
            repeated_band_consistency = stable_cases / len(comparable_cases)

    return {
        "decision": "PASS" if layer1_ok and layer2_ok and layer3_ok else "FAIL",
        "thresholds": {
            "structural_validity": 1.0,
            "age_exact_match": EXACT_MATCH_THRESHOLD,
            "horizon_exact_match": EXACT_MATCH_THRESHOLD,
            "risk_exact_match": EXACT_MATCH_THRESHOLD,
            "risk_band_accuracy": 1.0,
            "unsupported_guesses": 0,
        },
        "metrics": {
            "case_count": len(cases),
            "runs_per_case": repeats,
            "total_runs": total_runs,
            "layer1_structural": {
                "passed": layer1_passed,
                "total": total_runs,
                "decision": "PASS" if layer1_ok else "FAIL",
            },
            "layer2_invariants": {
                "passed": layer2_properties_passed,
                "total": total_runs,
                "age_exact_match": accuracies["age"],
                "horizon_exact_match": accuracies["horizon"],
                "case_results_all_checks_passed": layer2_passed,
                "decision": "PASS" if layer2_ok else "FAIL",
            },
            "layer3_risk_semantics": {
                "passed": layer3_band_passed,
                "total": total_runs,
                "risk_exact_match": accuracies["risk"],
                "risk_band_accuracy": (
                    risk_band_matches / (scored_cases["risk"] * repeats)
                    if scored_cases["risk"]
                    else 0.0
                ),
                "exact_case_results_passed": layer3_passed,
                "unsupported_guess_count": unsupported_guess_count,
                "repeated_band_consistency": repeated_band_consistency,
                "decision": "PASS" if layer3_ok else "FAIL",
            },
        },
        "cases": [record.to_dict() for record in case_results],
    }


def _load_adapter(specification: str) -> ModelAdapter:
    if ":" not in specification:
        raise ValueError("Adapter must use the module:factory format.")
    module_name, factory_name = specification.split(":", maxsplit=1)
    if not module_name or not factory_name:
        raise ValueError("Adapter must use the module:factory format.")
    module = importlib.import_module(module_name)
    factory: Callable[[], object] = getattr(module, factory_name)
    adapter = factory()
    if not callable(getattr(adapter, "extract", None)):
        raise TypeError("Adapter factory must return an object with extract().")
    return cast(ModelAdapter, adapter)


def _blocked_report(
    code: str,
    message: str,
    case_count: int = 0,
) -> dict[str, object]:
    return {
        "decision": "FAIL",
        "error": {"code": code, "message": message},
        "metrics": {
            "case_count": case_count,
            "layer1_structural": {"decision": "NOT_RUN"},
            "layer2_invariants": {"decision": "NOT_RUN"},
            "layer3_risk_semantics": {"decision": "NOT_RUN"},
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument(
        "--adapter",
        help="Adapter factory as module:factory. No model provider is selected by default.",
    )
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args(argv)

    try:
        cases = load_dataset(args.dataset)
        if not args.adapter:
            report = _blocked_report(
                "adapter_not_configured",
                "Configure an approved model adapter with --adapter module:factory.",
                case_count=len(cases),
            )
        else:
            adapter = _load_adapter(args.adapter)
            report = evaluate_cases(cases, adapter, repeats=args.repeats)
    except (
        ValueError,
        ImportError,
        AttributeError,
        TypeError,
        ExtractionError,
    ) as error:
        report = _blocked_report(
            getattr(error, "code", "evaluation_configuration_error"),
            str(error) if isinstance(error, ValueError) else error.__class__.__name__,
        )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["decision"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
