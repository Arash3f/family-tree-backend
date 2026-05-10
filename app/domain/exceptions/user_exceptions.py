from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class UserNotFoundException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(code=ErrorCode.USER_NOT_FOUND, status_code=404, detail=detail)


class UserPasswordIncorectException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.USER_PASSWORD_INCORECT, status_code=404, detail=detail
        )
