from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.shared.dto.role_filter_dto import RoleSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)


class RoleModel(BaseModel):
    id: UUID
    name: str
    permission_ids: list[UUID] = []
    user_count: int = 0


class _RoleUpdateDateRequest(BaseModel):
    name: str | None = None
    permission_ids: list[UUID] | None = None


class _RoleUpdateWhereRequest(BaseModel):
    role_id: UUID


class RoleUpdateRequest(BaseModel):
    data: _RoleUpdateDateRequest
    where: _RoleUpdateWhereRequest


class RoleUpdateResponse(BaseModel):
    id: UUID
    name: str
    permission_ids: list[UUID] = []


class RoleGetResponse(BaseModel):
    id: UUID
    name: str
    permission_ids: list[UUID] = []


class RoleCreateRequest(BaseModel):
    name: str | None
    permission_ids: list[UUID] | None


class RoleCreateResponse(BaseModel):
    id: UUID
    name: str
    permission_ids: list[UUID] = []


class RoleFilterRequestData(BaseModel):
    id: UUID | None = None
    name: str | None = None
    permission_id: UUID | None = None


class FilterRoleRequest(BaseModel):
    pagination: PaginationRequestParams = Field(default_factory=PaginationRequestParams)
    filters: RoleFilterRequestData | None = None
    sort: SortRequestParams[RoleSortField] = Field(
        default_factory=lambda: SortRequestParams(
            sort_order=SortOrderField.DESC,
            sort_by=RoleSortField.ID,
        )
    )
