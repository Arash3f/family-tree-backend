from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class RoleNotFoundException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(code=ErrorCode.ROLE_NOT_FOUND, status_code=404, detail=detail)
