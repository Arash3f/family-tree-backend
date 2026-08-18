from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.sorter_dto import SortParams


class RoleSortField(StrEnum):
    ID = "id"
    NAME = "name"


class RoleFilterDTO(BaseModel):
    id: UUID | None = None
    name: str | None = None
    permission_id: UUID | None = None


class FilterRoleQuery(BaseModel):
    pagination: PaginationParams
    filters: RoleFilterDTO | None = None
    sort: SortParams[RoleSortField]
