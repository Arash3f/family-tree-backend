from datetime import date
from enum import Enum

import strawberry

from app.domain.entities.person import Gender as DomainGender
from app.domain.shared.dto.marriage_filter_dto import MarriageSortField
from app.domain.shared.dto.permission_filter_dto import PermissionSortField
from app.domain.shared.dto.person_filter_dto import PersonSortField
from app.domain.shared.dto.role_filter_dto import RoleSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.domain.shared.dto.user_filter_dto import UserSortField
from app.presentation.utils.date_convert import gregorian_to_jalali


@strawberry.enum(name="Gender")
class GenderEnum(Enum):
    MALE = "male"
    FEMALE = "female"


@strawberry.enum(name="SortOrder")
class SortOrderEnum(Enum):
    ASC = "asc"
    DESC = "desc"


@strawberry.enum(name="PersonSortBy")
class PersonSortByEnum(Enum):
    ID = "id"
    NAME = "name"
    BIRTH_DAY = "birth_date"
    GENDER = "gender"


@strawberry.enum(name="UserSortBy")
class UserSortByEnum(Enum):
    ID = "id"
    USERNAME = "username"
    ROLE_ID = "role_id"


@strawberry.enum(name="RoleSortBy")
class RoleSortByEnum(Enum):
    ID = "id"
    NAME = "name"


@strawberry.enum(name="PermissionSortBy")
class PermissionSortByEnum(Enum):
    ID = "id"
    NAME = "name"


@strawberry.enum(name="MarriageSortBy")
class MarriageSortByEnum(Enum):
    ID = "id"
    MARRIED_AT = "married_at"
    DIVORCED_AT = "divorced_at"


def to_domain_gender(value: GenderEnum | DomainGender) -> DomainGender:
    if isinstance(value, DomainGender):
        return value
    return DomainGender(value.value)


def to_gender_enum(value: DomainGender | str) -> GenderEnum:
    raw = value.value if isinstance(value, DomainGender) else value
    return GenderEnum(raw)


def to_sort_order(value: SortOrderEnum | None) -> SortOrderField:
    if value is None:
        return SortOrderField.DESC
    return SortOrderField(value.value)


def format_jalali_date(value: date | None) -> str | None:
    if value is None:
        return None
    return gregorian_to_jalali(value)


@strawberry.type
class ResultType:
    result: str


@strawberry.input
class PaginationInput:
    page: int = 1
    page_size: int = 30
    offset: int = 0


@strawberry.input
class DateRangeInput:
    min: date | None = None
    max: date | None = None


@strawberry.input
class JalaliDateRangeInput:
    """Date range using Jalali strings (YYYY/MM/DD), matching REST person filters."""

    min: str | None = None
    max: str | None = None


def person_sort_field(value: PersonSortByEnum | None) -> PersonSortField:
    return PersonSortField((value or PersonSortByEnum.ID).value)


def user_sort_field(value: UserSortByEnum | None) -> UserSortField:
    return UserSortField((value or UserSortByEnum.ID).value)


def role_sort_field(value: RoleSortByEnum | None) -> RoleSortField:
    return RoleSortField((value or RoleSortByEnum.ID).value)


def permission_sort_field(value: PermissionSortByEnum | None) -> PermissionSortField:
    return PermissionSortField((value or PermissionSortByEnum.ID).value)


def marriage_sort_field(value: MarriageSortByEnum | None) -> MarriageSortField:
    return MarriageSortField((value or MarriageSortByEnum.ID).value)


def pagination_dict(pagination: PaginationInput | None) -> dict:
    p = pagination or PaginationInput()
    return {"page": p.page, "page_size": p.page_size, "offset": p.offset}
