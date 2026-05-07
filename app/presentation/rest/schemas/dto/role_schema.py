from typing import List

from pydantic import BaseModel

from app.domain.shared.dto.role_filter_dto import RoleSortField
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)


class RoleModel(BaseModel):
    id: int
    name: str
    permission_ids: List[int] | None = []


class _RoleUpdateDateRequest(BaseModel):
    name: str | None
    permission_ids: List[int] | None


class _RoleUpdateWhereRequest(BaseModel):
    role_id: int


class RoleUpdateRequest(BaseModel):
    data: _RoleUpdateDateRequest
    where: _RoleUpdateWhereRequest


class RoleUpdateResponse(BaseModel):
    id: int
    name: str
    permission_ids: List[int] = []


class RoleGetResponse(BaseModel):
    id: int
    name: str
    permission_ids: List[int] = []


class RoleCreateRequest(BaseModel):
    name: str | None
    permission_ids: List[int] | None


class RoleCreateResponse(BaseModel):
    id: int
    name: str
    permission_ids: List[int] = []


class RoleFilterRequestData(BaseModel):
    id: int | None = None
    name: str | None = None
    permission_id: int | None = None


class FilterRoleRequest(BaseModel):
    pagination: PaginationRequestParams
    filters: RoleFilterRequestData
    sort: SortRequestParams[RoleSortField]
