from app.utils.error_codes import ErrorCode


class AppException(Exception):
    """
    Base application-specific exception class.

    This is the root exception type used across the application for
    all controlled (expected) error conditions. It provides a
    standardized structure for error handling and allows the global
    exception handler to produce consistent JSON responses.
    """

    def __init__(
        self, code: ErrorCode, status_code: int = 400, detail: list[str] | None = None
    ):
        self.detail = detail or []
        self.code = code
        self.status_code = status_code
