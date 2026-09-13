from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class UserNotFoundException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.USER_NOT_FOUND, status_code=404, detail=detail or []
        )


class UserPasswordIncorectException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.USER_PASSWORD_INCORECT, status_code=401, detail=detail
        )


class PasswordConfirmationMismatchException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.PASSWORD_CONFIRMATION_MISMATCH,
            status_code=422,
            detail=detail or ["password and re_password must match"],
        )


class SelfRoleChangeException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.SELF_ROLE_CHANGE,
            status_code=403,
            detail=detail or ["a user cannot change their own role"],
        )


class PrivilegedUserModificationException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.PRIVILEGED_USER_MODIFICATION,
            status_code=403,
            detail=detail or ["administrator role changes require an administrator"],
        )


class UsernameAlreadyExistsException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.USERNAME_ALREADY_EXISTS,
            status_code=409,
            detail=detail or ["username is already taken"],
        )


class EmailAlreadyExistsException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.EMAIL_ALREADY_EXISTS,
            status_code=409,
            detail=detail or ["email is already registered"],
        )


class AccountDeactivatedException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.ACCOUNT_DEACTIVATED,
            status_code=403,
            detail=detail or ["account has been deactivated"],
        )
