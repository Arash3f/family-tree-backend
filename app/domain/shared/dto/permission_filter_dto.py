from enum import Enum
from pydantic import BaseModel
from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.sorter_dto import SortParams


class PermissionSortField(str, Enum):
    ID = "id"
    NAME = "name"


class PermissionFilterDTO(BaseModel):
    id: int | None
    name: str | None


class FilterPermissionQuery(BaseModel):
    pagination: PaginationParams
    filters: PermissionFilterDTO | None = None
    sort: SortParams[PermissionSortField]
