from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class FamilyTreeNotFoundException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.FAMILY_TREE_NOT_FOUND,
            status_code=404,
            detail=detail or [],
        )


class TreeMembershipDeniedException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.TREE_MEMBERSHIP_DENIED,
            status_code=403,
            detail=detail or [],
        )


class TreeOwnerRequiredException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.TREE_OWNER_REQUIRED,
            status_code=403,
            detail=detail or [],
        )


class TreeMemberAlreadyExistsException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.TREE_MEMBER_ALREADY_EXISTS,
            status_code=409,
            detail=detail or [],
        )


class TreeMemberNotFoundException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.TREE_MEMBER_NOT_FOUND,
            status_code=404,
            detail=detail or [],
        )


class CannotRemoveLastOwnerException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.CANNOT_REMOVE_LAST_OWNER,
            status_code=422,
            detail=detail or [],
        )


class TreeAccessDeniedException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.TREE_ACCESS_DENIED,
            status_code=403,
            detail=detail or [],
        )


class PersonTreeMismatchException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.PERSON_TREE_MISMATCH,
            status_code=404,
            detail=detail or [],
        )


class MarriageTreeMismatchException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.MARRIAGE_TREE_MISMATCH,
            status_code=404,
            detail=detail or [],
        )


class TreeExcelInvalidException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.TREE_EXCEL_INVALID,
            status_code=422,
            detail=detail or [],
        )


class TreeExcelEmptyException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.TREE_EXCEL_EMPTY,
            status_code=422,
            detail=detail or [],
        )


class FreeAccountLimitException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.FREE_ACCOUNT_LIMIT,
            status_code=403,
            detail=detail or [],
        )
