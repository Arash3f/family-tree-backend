from pydantic import BaseModel

from app.domain.shared.dto.user_filter_dto import UserSortField
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)


class UserModel(BaseModel):
    id: int
    username: str
    role_id: int | None = None


class _UserUpdateDateRequest(BaseModel):
    username: str | None = None
    password: str | None = None
    re_password: str | None = None
    role_id: int | None = None


class _UserUpdateWhereRequest(BaseModel):
    user_id: int


class UserUpdateRequest(BaseModel):
    data: _UserUpdateDateRequest
    where: _UserUpdateWhereRequest


class UserUpdateResponse(BaseModel):
    id: int
    username: str
    role_id: int | None


class UserGetResponse(BaseModel):
    id: int
    username: str
    role_id: int | None


class UserCreateRequest(BaseModel):
    username: str
    password: str
    re_password: str
    role_id: int | None = None


class UserCreateResponse(BaseModel):
    id: int
    username: str
    role_id: int | None


class UserFilterRequestData(BaseModel):
    id: int | None = None
    username: str | None = None
    role_id: int | None = None


class FilterUserRequest(BaseModel):
    pagination: PaginationRequestParams
    filters: UserFilterRequestData
    sort: SortRequestParams[UserSortField]
