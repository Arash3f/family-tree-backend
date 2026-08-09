from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class SelfMarriageException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.SELF_MARRIAGE, status_code=422, detail=detail or []
        )


class DivorceBeforeMarriageException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.DIVORCED_BEFORE_MARRIAGE,
            status_code=422,
            detail=detail or [],
        )


class MarriageAfterDivorceException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.MARRIAGE_AFTER_DIVORCE, status_code=422, detail=detail or []
        )


class UnderageMarriageException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.UNDERAGE_MARRIAGE, status_code=422, detail=detail or []
        )


class MarriageNotFoundException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.MARRIAGE_NOT_FOUND, status_code=404, detail=detail or []
        )


class InvalidMarriageGenderException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.INVALID_MARRIAGE_GENDER, status_code=422, detail=detail or []
        )


class ActiveMarriageExistsException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.ACTIVE_MARRIAGE_EXISTS, status_code=422, detail=detail or []
        )


class MarriageAlreadyDivorcedException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.MARRIAGE_ALREADY_DIVORCED,
            status_code=422,
            detail=detail or [],
        )
