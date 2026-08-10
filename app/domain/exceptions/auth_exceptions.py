from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class InvalidCredentialsException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.InvalidCredentials, status_code=401, detail=detail
        )


class SessionNotFoundException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.SESSION_NOT_FOUND,
            status_code=404,
            detail=detail or ["session not found"],
        )
