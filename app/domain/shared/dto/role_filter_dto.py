from enum import Enum
from pydantic import BaseModel
from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.sorter_dto import SortParams


class RoleSortField(str, Enum):
    ID = "id"
    NAME = "name"


class RoleFilterDTO(BaseModel):
    id: int | None = None
    name: str | None = None
    permission_id: int | None = None


class FilterRoleQuery(BaseModel):
    pagination: PaginationParams
    filters: RoleFilterDTO | None = None
    sort: SortParams[RoleSortField]
