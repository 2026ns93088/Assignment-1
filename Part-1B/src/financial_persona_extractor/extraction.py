"""Provider-neutral extraction orchestration."""

from financial_persona_extractor.errors import AdapterNotConfiguredError
from financial_persona_extractor.model_adapter import ModelAdapter
from financial_persona_extractor.policy import validate_result_invariants
from financial_persona_extractor.schemas import ExtractionResult, validate_structure


def extract_persona(
    biography: str,
    adapter: ModelAdapter | None = None,
) -> ExtractionResult:
    """Extract and validate a persona without silently selecting a provider."""
    if not isinstance(biography, str):
        raise TypeError("biography must be a string.")
    if adapter is None:
        raise AdapterNotConfiguredError()

    candidate = adapter.extract(biography)
    result = validate_structure(candidate)
    validate_result_invariants(result)
    return result
