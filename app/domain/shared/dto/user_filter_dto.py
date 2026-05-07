from enum import Enum
from pydantic import BaseModel
from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.sorter_dto import SortParams


class UserSortField(str, Enum):
    ID = "id"
    USERNAME = "username"
    ROLE_ID = "role_id"


class UserFilterDTO(BaseModel):
    id: int | None = None
    username: str | None = None
    role_id: int | None = None


class FilterUserQuery(BaseModel):
    pagination: PaginationParams
    filters: UserFilterDTO | None = None
    sort: SortParams[UserSortField]
