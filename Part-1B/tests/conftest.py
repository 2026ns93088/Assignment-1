from collections.abc import Mapping, Sequence

import pytest

from financial_persona_extractor.evaluation import EvaluationCase
from financial_persona_extractor.schemas import ExtractionStatus


class ScriptedAdapter:
    def __init__(self, responses: Sequence[Mapping[str, object]]) -> None:
        self._responses = iter(responses)

    def extract(
        self,
        biography: str,
        instructions: str = "",
    ) -> Mapping[str, object]:
        del biography, instructions
        return next(self._responses)


@pytest.fixture
def scripted_adapter_factory():
    return ScriptedAdapter


@pytest.fixture
def evaluation_cases():
    return [
        EvaluationCase(
            case_id=1,
            category="Normal",
            input_text="I am 34 years old and invest for 12 years, with conservative risk.",
            expected_status=ExtractionStatus.COMPLETE,
            expected_age=34,
            expected_horizon=12,
            expected_risk=2,
        ),
        EvaluationCase(
            case_id=2,
            category="Missing risk",
            input_text="I am 35 and invest for 10 years.",
            expected_status=ExtractionStatus.CLARIFICATION_REQUIRED,
            expected_age=35,
            expected_horizon=10,
            expected_risk=None,
        ),
    ]
