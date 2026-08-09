from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class SelfParentException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(code=ErrorCode.SELF_PARENT, status_code=422, detail=detail)


class SameParentException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(code=ErrorCode.SAME_PARENT, status_code=422, detail=detail)


class InvalidBirthDateException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.INVALID_BIRTH_DAY, status_code=423, detail=detail
        )


class InvalidPersonGenderException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(code=ErrorCode.INVALID_GENDER, status_code=423, detail=detail)


class TooManyBiologicalParentsException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.TOO_MANY_BIOLOGICAL_PARENTS,
            status_code=422,
            detail=detail or ["child cannot have more than two biological parents"],
        )


class InvalidParentMarriageException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.INVALID_PARENT_MARRIAGE,
            status_code=422,
            detail=detail
            or ["biological parents must match the origin marriage spouses"],
        )


class HusbandNotFoundException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(
            code=ErrorCode.HUSBAND_NOT_FOUND, status_code=404, detail=detail
        )


class WifeNotFoundException(AppException):
    def __init__(self, detail: list[str] = []):
        super().__init__(code=ErrorCode.WIFE_NOT_FOUND, status_code=404, detail=detail)


class PersonNotFoundException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.PERSON_NOT_FOUND, status_code=404, detail=detail
        )


class PersonHasMarriagesException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.PERSON_HAS_MARRIAGES, status_code=422, detail=detail
        )


class PersonHasChildrenException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.PERSON_HAS_CHILDREN, status_code=422, detail=detail
        )
