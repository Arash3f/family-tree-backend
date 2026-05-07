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
    id: int | None = None
    name: str | None = None
    gender: Gender | None = None
    birth_date: RangeDTO[date] | None = None
    father_id: int | None = None
    mother_id: int | None = None


class FilterPersonQuery(BaseModel):
    pagination: PaginationParams
    filters: PersonFilterDTO | None
    sort: SortParams[PersonSortField]
