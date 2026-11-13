import importlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from financial_persona_extractor.evaluation import (
    EvaluationCase,
    evaluate_cases,
    load_dataset,
    main,
)
from financial_persona_extractor.schemas import ExtractionStatus


def result(
    *,
    age,
    horizon,
    risk,
    questions=None,
):
    unresolved = age is None or horizon is None or risk is None
    return {
        "status": ("clarification_required" if unresolved else "complete"),
        "age": age,
        "investment_horizon_years": horizon,
        "risk_tolerance_score": risk,
        "clarification_questions": questions or [],
    }


class MappingAdapter:
    def __init__(self, outputs):
        self.outputs = iter(outputs)

    def extract(self, biography, instructions=""):
        del biography, instructions
        return next(self.outputs)


def test_dataset_has_exactly_fifteen_valid_cases():
    cases = load_dataset()
    assert len(cases) == 15
    assert [case.case_id for case in cases] == list(range(1, 16))


def test_empty_evaluation_set_is_rejected():
    with pytest.raises(ValueError, match="At least one evaluation case"):
        evaluate_cases([], MappingAdapter([]))


def test_mock_adapter_executes_all_fifteen_cases(monkeypatch):
    harness_path = Path(__file__).resolve().parents[2] / ".harness"
    monkeypatch.syspath_prepend(str(harness_path))
    mock_adapter = importlib.import_module("mock_adapter")

    report = evaluate_cases(load_dataset(), mock_adapter.create_adapter())

    assert report["decision"] == "PASS"
    assert report["metrics"]["case_count"] == 15
    assert report["metrics"]["layer1_structural"]["decision"] == "PASS"
    assert report["metrics"]["layer2_invariants"]["decision"] == "PASS"
    assert report["metrics"]["layer3_risk_semantics"]["decision"] == "PASS"
    assert report["metrics"]["layer3_risk_semantics"]["risk_exact_match"] == 1.0


def test_cli_without_approved_adapter_returns_explicit_fail(capsys):
    assert main([]) == 1
    report = json.loads(capsys.readouterr().out)

    assert report["decision"] == "FAIL"
    assert report["error"]["code"] == "adapter_not_configured"
    assert report["metrics"]["case_count"] == 15
    assert report["metrics"]["layer1_structural"]["decision"] == "NOT_RUN"


def test_three_layer_evaluation_passes_valid_examples(evaluation_cases):
    adapter = MappingAdapter(
        [
            result(age=34, horizon=12, risk=2),
            result(
                age=35,
                horizon=10,
                risk=None,
                questions=["What is your risk tolerance?"],
            ),
        ]
    )
    report = evaluate_cases(evaluation_cases, adapter)
    assert report["decision"] == "PASS"
    assert report["metrics"]["layer1_structural"]["decision"] == "PASS"
    assert report["metrics"]["layer2_invariants"]["decision"] == "PASS"
    assert report["metrics"]["layer3_risk_semantics"]["decision"] == "PASS"


def test_wrong_risk_band_fails_semantic_layer(evaluation_cases):
    adapter = MappingAdapter(
        [
            result(age=34, horizon=12, risk=9),
            result(
                age=35,
                horizon=10,
                risk=None,
                questions=["What is your risk tolerance?"],
            ),
        ]
    )
    report = evaluate_cases(evaluation_cases, adapter)
    assert report["decision"] == "FAIL"
    assert report["metrics"]["layer3_risk_semantics"]["decision"] == "FAIL"


def test_exact_match_threshold_allows_up_to_five_percent_misses():
    template = EvaluationCase(
        case_id=1,
        category="Qualitative risk conservative",
        input_text="I prefer safe returns.",
        expected_status=ExtractionStatus.COMPLETE,
        expected_age=34,
        expected_horizon=12,
        expected_risk=2,
    )
    cases = [replace(template, case_id=case_id) for case_id in range(1, 21)]
    outputs = [
        result(
            age=case.expected_age,
            horizon=case.expected_horizon,
            risk=3 if case.case_id == 1 else case.expected_risk,
        )
        for case in cases
    ]

    report = evaluate_cases(cases, MappingAdapter(outputs))

    assert report["decision"] == "PASS"
    assert report["metrics"]["layer3_risk_semantics"]["risk_exact_match"] == 0.95


def test_guess_for_missing_risk_fails_semantic_layer(evaluation_cases):
    adapter = MappingAdapter(
        [
            result(age=34, horizon=12, risk=2),
            result(
                age=35,
                horizon=10,
                risk=4,
                questions=[],
            ),
        ]
    )
    report = evaluate_cases(evaluation_cases, adapter)
    assert report["decision"] == "FAIL"
    assert report["metrics"]["layer3_risk_semantics"]["unsupported_guess_count"] == 1


@pytest.mark.parametrize(
    ("field", "question"),
    [
        ("age", "What is your age?"),
        ("horizon", "What is your investment horizon?"),
    ],
)
def test_guess_for_missing_age_or_horizon_fails_invariant_layer(
    evaluation_cases,
    field,
    question,
):
    case = evaluation_cases[1]
    if field == "age":
        case = replace(case, expected_age=None)
        age, horizon = 35, 10
    else:
        case = replace(case, expected_horizon=None)
        age, horizon = 35, 10
    questions = [question, "What is your risk tolerance?"]
    adapter = MappingAdapter(
        [
            result(age=age, horizon=horizon, risk=None, questions=questions),
        ]
    )

    report = evaluate_cases([case], adapter)

    assert report["decision"] == "FAIL"
    assert report["metrics"]["layer2_invariants"]["decision"] == "FAIL"


def test_missing_clarification_question_fails_invariant_layer(evaluation_cases):
    adapter = MappingAdapter(
        [
            result(age=34, horizon=12, risk=2),
            result(
                age=35,
                horizon=10,
                risk=None,
                questions=["Please clarify."],
            ),
        ]
    )
    report = evaluate_cases(evaluation_cases, adapter)
    assert report["decision"] == "FAIL"
    assert report["metrics"]["layer2_invariants"]["decision"] == "FAIL"


def test_invalid_structure_fails_layer_one_and_aggregate(evaluation_cases):
    adapter = MappingAdapter(
        [
            {"status": "complete"},
            result(
                age=35,
                horizon=10,
                risk=None,
                questions=["What is your risk tolerance?"],
            ),
        ]
    )
    report = evaluate_cases(evaluation_cases, adapter)
    assert report["decision"] == "FAIL"
    assert report["metrics"]["layer1_structural"]["decision"] == "FAIL"
    assert report["cases"][0]["layer1"] == "FAIL"


def test_non_deterministic_scores_in_same_band_are_reported(evaluation_cases):
    class RepeatingAdapter:
        def __init__(self):
            self.count = 0

        def extract(self, biography, instructions=""):
            del biography, instructions
            self.count += 1
            if self.count % 2:
                return result(age=34, horizon=12, risk=2)
            return result(age=34, horizon=12, risk=3)

    one_case = evaluation_cases[:1]
    report = evaluate_cases(one_case, RepeatingAdapter(), repeats=2)
    metrics = report["metrics"]["layer3_risk_semantics"]
    assert metrics["risk_band_accuracy"] == 1.0
    assert metrics["repeated_band_consistency"] == 1.0


def test_expected_status_translation_uses_contract_status(evaluation_cases):
    assert evaluation_cases[0].expected_status is ExtractionStatus.COMPLETE
