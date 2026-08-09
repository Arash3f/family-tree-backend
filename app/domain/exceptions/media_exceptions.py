from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class InvalidMediaContentTypeException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.INVALID_MEDIA_CONTENT_TYPE,
            status_code=422,
            detail=detail,
        )


class MediaTooLargeException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.MEDIA_TOO_LARGE,
            status_code=413,
            detail=detail,
        )


class InvalidMediaObjectKeyException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.INVALID_MEDIA_OBJECT_KEY,
            status_code=422,
            detail=detail,
        )


class MediaObjectNotFoundException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.MEDIA_OBJECT_NOT_FOUND,
            status_code=404,
            detail=detail,
        )
