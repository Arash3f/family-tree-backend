from pydantic import BaseModel

from app.domain.shared.dto.permission_filter_dto import PermissionSortField
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)


class PermissionModel(BaseModel):
    id: int
    name: str


class PermissionFilterRequestData(BaseModel):
    id: int | None = None
    name: str | None = None


class FilterPermissionRequest(BaseModel):
    pagination: PaginationRequestParams
    filters: PermissionFilterRequestData | None = None
    sort: SortRequestParams[PermissionSortField]
