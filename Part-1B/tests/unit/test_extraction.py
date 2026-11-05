import pytest

from financial_persona_extractor.errors import (
    AdapterNotConfiguredError,
    InvalidModelOutputError,
    ModelAdapterError,
)
from financial_persona_extractor.extraction import extract_persona


class ValidAdapter:
    def extract(self, biography, instructions=""):
        del biography, instructions
        return {
            "status": "complete",
            "age": 34,
            "investment_horizon_years": 12,
            "risk_tolerance_score": 8,
            "clarification_questions": [],
        }


def test_extraction_uses_injected_adapter_and_validates_result():
    result = extract_persona("I am 34 and prefer aggressive growth.", ValidAdapter())
    assert result.risk_tolerance_score == 8


def test_no_provider_is_selected_implicitly():
    with pytest.raises(AdapterNotConfiguredError):
        extract_persona("Private biography")


def test_invalid_model_output_fails_explicitly():
    class InvalidAdapter:
        def extract(self, biography, instructions=""):
            del biography, instructions
            return {"status": "complete"}

    with pytest.raises(InvalidModelOutputError):
        extract_persona("Biography", InvalidAdapter())


def test_adapter_operational_failure_is_not_a_success_result():
    class FailingAdapter:
        def extract(self, biography, instructions=""):
            del biography, instructions
            raise ModelAdapterError("provider_failure", "Provider unavailable.")

    with pytest.raises(ModelAdapterError):
        extract_persona("Biography", FailingAdapter())


def test_non_string_biography_is_rejected():
    with pytest.raises(TypeError):
        extract_persona(12, ValidAdapter())
