from datetime import datetime
from enum import Enum
from uuid import UUID

import strawberry

from app.domain.shared.account_type import AccountType as DomainAccountType
from app.presentation.graphql.types.common import (
    PaginationInput,
    SortOrderEnum,
    UserSortByEnum,
)


@strawberry.enum
class AccountTypeEnum(Enum):
    FREE = "free"
    PAID = "paid"


def _account_type_enum(value: DomainAccountType | str | None) -> AccountTypeEnum:
    if value is None:
        return AccountTypeEnum.FREE
    raw = value.value if isinstance(value, DomainAccountType) else str(value)
    return AccountTypeEnum(raw)


@strawberry.type
class UserType:
    id: UUID
    username: str
    fullname: str
    role_id: UUID | None = None
    account_type: AccountTypeEnum = AccountTypeEnum.FREE
    last_session_at: datetime | None = None


@strawberry.type
class UserPage:
    items: list[UserType]
    total: int
    page: int
    page_size: int


@strawberry.type
class AuthTokensType:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@strawberry.input
class UserCreateInput:
    username: str
    fullname: str
    password: str
    re_password: str
    role_id: UUID | None = None
    account_type: AccountTypeEnum | None = None


@strawberry.input
class UserUpdateDataInput:
    username: str | None = None
    fullname: str | None = None
    password: str | None = None
    re_password: str | None = None
    role_id: UUID | None = None
    account_type: AccountTypeEnum | None = None


@strawberry.input
class UserUpdateWhereInput:
    user_id: UUID


@strawberry.input
class UserUpdateInput:
    data: UserUpdateDataInput
    where: UserUpdateWhereInput


@strawberry.input
class UserFilterInput:
    id: UUID | None = None
    username: str | None = None
    role_id: UUID | None = None


@strawberry.input
class UserListInput:
    pagination: PaginationInput | None = None
    filters: UserFilterInput | None = None
    sort_order: SortOrderEnum | None = None
    sort_by: UserSortByEnum | None = None


def user_from_mapping(data: dict) -> UserType:
    return UserType(
        id=data["id"],
        username=data["username"],
        fullname=data["fullname"],
        role_id=data.get("role_id"),
        account_type=_account_type_enum(data.get("account_type")),
        last_session_at=data.get("last_session_at"),
    )
