from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class InvalidCredentialsException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.InvalidCredentials, status_code=401, detail=detail
        )
