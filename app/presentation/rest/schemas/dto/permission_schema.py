from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.shared.dto.permission_filter_dto import PermissionSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)


class PermissionModel(BaseModel):
    id: UUID
    name: str


class PermissionFilterRequestData(BaseModel):
    id: UUID | None = None
    name: str | None = None


class FilterPermissionRequest(BaseModel):
    pagination: PaginationRequestParams = Field(default_factory=PaginationRequestParams)
    filters: PermissionFilterRequestData | None = None
    sort: SortRequestParams[PermissionSortField] = Field(
        default_factory=lambda: SortRequestParams(
            sort_order=SortOrderField.DESC,
            sort_by=PermissionSortField.ID,
        )
    )
