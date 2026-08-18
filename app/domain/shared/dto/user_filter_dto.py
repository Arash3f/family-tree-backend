from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.sorter_dto import SortParams


class UserSortField(StrEnum):
    ID = "id"
    USERNAME = "username"
    ROLE_ID = "role_id"


class UserFilterDTO(BaseModel):
    id: UUID | None = None
    username: str | None = None
    role_id: UUID | None = None


class FilterUserQuery(BaseModel):
    pagination: PaginationParams
    filters: UserFilterDTO | None = None
    sort: SortParams[UserSortField]
