"""HTTP-facing errors shared by request parsing and the API layer."""


class APIError(Exception):
    """An expected API error with a stable HTTP response contract."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
