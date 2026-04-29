from app.presentation.utils.app_exception import AppException
from app.presentation.utils.error_codes import ErrorCode


class SelfMarriageException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(code=ErrorCode.SELF_MARRIAGE, status_code=422, detail=detail)


class DivorceBeforeMarriageException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.DIVORCED_BEFORE_MARRIAGE, status_code=422, detail=detail
        )


class MarriageAfterDivorceException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.MARRIAGE_AFTER_DIVORCE, status_code=422, detail=detail
        )


class UnderageMarriageException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.UNDERAGE_MARRIAGE, status_code=422, detail=detail
        )


class InvalidMarriageGenderException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.INVALID_MARRIAGE_GENDER, status_code=422, detail=detail
        )


class MarriageNotFoundException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.MARRIAGE_NOT_FOUND, status_code=404, detail=detail
        )
