"""Cross-field invariants and clarification policy."""

import re

from financial_persona_extractor.errors import InvalidModelOutputError
from financial_persona_extractor.schemas import ExtractionResult, ExtractionStatus

_FIELD_QUESTION_MARKERS = {
    "age": re.compile(r"\bage\b|\bhow old\b", re.IGNORECASE),
    "investment_horizon_years": re.compile(
        r"\binvest(?:ment|ing)?\b|\bhorizon\b",
        re.IGNORECASE,
    ),
    "risk_tolerance_score": re.compile(
        r"\brisk\b|\bvolatility\b|\bloss(?:es)?\b",
        re.IGNORECASE,
    ),
}


def unresolved_fields(result: ExtractionResult) -> tuple[str, ...]:
    fields = (
        ("age", result.age),
        ("investment_horizon_years", result.investment_horizon_years),
        ("risk_tolerance_score", result.risk_tolerance_score),
    )
    return tuple(name for name, value in fields if value is None)


def question_addresses_field(question: str, field: str) -> bool:
    return bool(_FIELD_QUESTION_MARKERS[field].search(question))


def validate_result_invariants(result: ExtractionResult) -> None:
    """Validate status/null/question consistency and question targeting."""
    unresolved = unresolved_fields(result)
    if result.status is ExtractionStatus.COMPLETE:
        if unresolved:
            raise InvalidModelOutputError(
                "complete status requires all three extracted values."
            )
        if result.clarification_questions:
            raise InvalidModelOutputError(
                "complete status requires an empty clarification_questions array."
            )
        return

    if not unresolved:
        raise InvalidModelOutputError(
            "clarification_required status requires at least one null field."
        )
    if not result.clarification_questions:
        raise InvalidModelOutputError(
            "Unresolved fields require targeted clarification questions."
        )

    for field in unresolved:
        if not any(
            question_addresses_field(question, field)
            for question in result.clarification_questions
        ):
            raise InvalidModelOutputError(
                f"An unresolved {field} requires a specific clarification question."
            )

    for question in result.clarification_questions:
        if not any(question_addresses_field(question, field) for field in unresolved):
            raise InvalidModelOutputError(
                "Clarification questions must target an unresolved field."
            )
