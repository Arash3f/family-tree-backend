from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.shared.account_type import AccountType
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.domain.shared.dto.user_filter_dto import UserSortField
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)


class UserModel(BaseModel):
    id: UUID
    username: str
    fullname: str
    role_id: UUID | None = None
    account_type: AccountType = AccountType.FREE
    last_session_at: datetime | None = None


class _UserUpdateDateRequest(BaseModel):
    username: str | None = None
    fullname: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=256)
    re_password: str | None = Field(default=None, min_length=8, max_length=256)
    role_id: UUID | None = None
    account_type: AccountType | None = None


class _UserUpdateWhereRequest(BaseModel):
    user_id: UUID


class UserUpdateRequest(BaseModel):
    data: _UserUpdateDateRequest
    where: _UserUpdateWhereRequest


class UserUpdateResponse(BaseModel):
    id: UUID
    username: str
    fullname: str
    role_id: UUID | None
    account_type: AccountType


class UserGetResponse(BaseModel):
    id: UUID
    username: str
    fullname: str
    role_id: UUID | None
    account_type: AccountType


class UserCreateRequest(BaseModel):
    username: str
    fullname: str
    password: str = Field(min_length=8, max_length=256)
    re_password: str = Field(min_length=8, max_length=256)
    role_id: UUID | None = None
    account_type: AccountType = AccountType.FREE


class UserCreateResponse(BaseModel):
    id: UUID
    username: str
    fullname: str
    role_id: UUID | None
    account_type: AccountType


class UserFilterRequestData(BaseModel):
    id: UUID | None = None
    username: str | None = None
    role_id: UUID | None = None


class FilterUserRequest(BaseModel):
    pagination: PaginationRequestParams = Field(default_factory=PaginationRequestParams)
    filters: UserFilterRequestData | None = None
    sort: SortRequestParams[UserSortField] = Field(
        default_factory=lambda: SortRequestParams(
            sort_order=SortOrderField.DESC,
            sort_by=UserSortField.ID,
        )
    )
