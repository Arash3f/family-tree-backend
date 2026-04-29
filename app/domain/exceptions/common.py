from app.presentation.utils.app_exception import AppException
from app.presentation.utils.error_codes import ErrorCode


class UnExpectedIdException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(code=ErrorCode.UN_EXPECTED_ID, status_code=500, detail=detail)
