from app.presentation.utils.app_exception import AppException
from app.presentation.utils.error_codes import ErrorCode


class PermissionNotFoundException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.PERMISSION_NOT_FOUND, status_code=404, detail=detail
        )


class PermissionDeniedException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.PERMISSION_DENIED, status_code=403, detail=detail
        )
