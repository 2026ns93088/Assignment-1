"""Explicit failures raised by the extraction pipeline."""


class ExtractionError(Exception):
    """Base class for expected extraction failures."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class AdapterNotConfiguredError(ExtractionError):
    def __init__(self) -> None:
        super().__init__(
            "adapter_not_configured",
            "No model adapter has been configured.",
        )


class ModelAdapterError(ExtractionError):
    """A model adapter failed without producing a valid extraction."""


class InvalidModelOutputError(ExtractionError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_model_output", message)
