"""Strict public result schema and structural validation."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from financial_persona_extractor.errors import InvalidModelOutputError

RESULT_KEYS = frozenset(
    {
        "status",
        "age",
        "investment_horizon_years",
        "risk_tolerance_score",
        "clarification_questions",
    }
)


class ExtractionStatus(StrEnum):
    COMPLETE = "complete"
    CLARIFICATION_REQUIRED = "clarification_required"


@dataclass(frozen=True)
class ExtractionResult:
    status: ExtractionStatus
    age: int | None
    investment_horizon_years: int | None
    risk_tolerance_score: int | None
    clarification_questions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "age": self.age,
            "investment_horizon_years": self.investment_horizon_years,
            "risk_tolerance_score": self.risk_tolerance_score,
            "clarification_questions": list(self.clarification_questions),
        }


def _validate_optional_integer(
    data: Mapping[str, object],
    field: str,
    minimum: int,
    maximum: int | None = None,
) -> int | None:
    value = data[field]
    if value is None:
        return None
    if type(value) is not int:
        raise InvalidModelOutputError(f"{field} must be an integer or null.")
    if value < minimum or (maximum is not None and value > maximum):
        if maximum is None:
            requirement = f"greater than or equal to {minimum}"
        else:
            requirement = f"between {minimum} and {maximum}"
        raise InvalidModelOutputError(f"{field} must be {requirement}.")
    return value


def validate_structure(candidate: object) -> ExtractionResult:
    """Validate exact keys and strict JSON-compatible field types/domains."""
    if not isinstance(candidate, Mapping):
        raise InvalidModelOutputError("Model output must be a JSON object.")

    actual_keys = set(candidate)
    if actual_keys != RESULT_KEYS:
        missing = sorted(RESULT_KEYS - actual_keys)
        extra = sorted(actual_keys - RESULT_KEYS)
        details: list[str] = []
        if missing:
            details.append(f"missing keys: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected keys: {', '.join(str(key) for key in extra)}")
        raise InvalidModelOutputError("; ".join(details) + ".")

    raw_status = candidate["status"]
    try:
        status = ExtractionStatus(raw_status)
    except (ValueError, TypeError) as error:
        raise InvalidModelOutputError(
            "status must be 'complete' or 'clarification_required'."
        ) from error

    raw_questions = candidate["clarification_questions"]
    if not isinstance(raw_questions, list) or any(
        not isinstance(question, str) or not question.strip()
        for question in raw_questions
    ):
        raise InvalidModelOutputError(
            "clarification_questions must be an array of non-empty strings."
        )

    return ExtractionResult(
        status=status,
        age=_validate_optional_integer(candidate, "age", 1),
        investment_horizon_years=_validate_optional_integer(
            candidate,
            "investment_horizon_years",
            1,
        ),
        risk_tolerance_score=_validate_optional_integer(
            candidate,
            "risk_tolerance_score",
            1,
            10,
        ),
        clarification_questions=tuple(raw_questions),
    )
