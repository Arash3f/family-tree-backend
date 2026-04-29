from datetime import date
from enum import Enum

from pydantic import BaseModel

from app.domain.entities.person import Gender
from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.range_dto import RangeDTO
from app.domain.shared.dto.sorter_dto import SortParams


class PersonSortField(str, Enum):
    ID = "id"
    NAME = "name"
    BIRTH_DAY = "birth_date"
    GENDER = "gender"


class PersonFilterDTO(BaseModel):
    id: int | None
    name: str | None
    gender: Gender | None
    birth_date: RangeDTO[date]
    father_id: int | None
    mother_id: int | None


class FilterPersonQuery(BaseModel):
    pagination: PaginationParams
    filters: PersonFilterDTO
    sort: SortParams[PersonSortField]
