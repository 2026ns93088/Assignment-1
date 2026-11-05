import pytest

from financial_persona_extractor.errors import InvalidModelOutputError
from financial_persona_extractor.policy import validate_result_invariants
from financial_persona_extractor.schemas import (
    ExtractionStatus,
    validate_structure,
)


def complete_output():
    return {
        "status": "complete",
        "age": 34,
        "investment_horizon_years": 12,
        "risk_tolerance_score": 5,
        "clarification_questions": [],
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("age", True),
        ("age", 0),
        ("investment_horizon_years", 1.5),
        ("risk_tolerance_score", False),
        ("risk_tolerance_score", 11),
        ("status", "SUCCESS"),
        ("clarification_questions", "What is your age?"),
    ],
)
def test_invalid_field_types_and_values_are_rejected(field, value):
    output = complete_output()
    output[field] = value
    with pytest.raises(InvalidModelOutputError):
        validate_structure(output)


def test_exact_output_keys_are_required():
    output = complete_output()
    output["confidence"] = 0.9
    with pytest.raises(InvalidModelOutputError, match="unexpected keys"):
        validate_structure(output)


def test_complete_result_satisfies_invariants():
    result = validate_structure(complete_output())
    validate_result_invariants(result)
    assert result.status is ExtractionStatus.COMPLETE
    assert set(result.to_dict()) == {
        "status",
        "age",
        "investment_horizon_years",
        "risk_tolerance_score",
        "clarification_questions",
    }


def test_clarification_result_requires_targeted_questions():
    output = complete_output()
    output.update(
        status="clarification_required",
        age=None,
        clarification_questions=["What is your exact age in years?"],
    )
    result = validate_structure(output)
    validate_result_invariants(result)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"age": None}, "requires all three"),
        ({"clarification_questions": ["What is your risk tolerance?"]}, "empty"),
    ],
)
def test_complete_status_rejects_missing_fields_or_questions(changes, message):
    output = complete_output()
    output.update(changes)
    with pytest.raises(InvalidModelOutputError, match=message):
        validate_result_invariants(validate_structure(output))


def test_every_unresolved_field_requires_a_specific_question():
    output = complete_output()
    output.update(
        status="clarification_required",
        age=None,
        investment_horizon_years=None,
        clarification_questions=["What is your age in years?"],
    )
    with pytest.raises(InvalidModelOutputError, match="investment_horizon_years"):
        validate_result_invariants(validate_structure(output))
