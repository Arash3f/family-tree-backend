from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.person import Gender, ParentRelationshipType
from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.range_dto import RangeDTO
from app.domain.shared.dto.sorter_dto import SortParams


class PersonSortField(StrEnum):
    ID = "id"
    NAME = "name"
    BIRTH_DAY = "birth_date"
    GENDER = "gender"


class PersonFilterDTO(BaseModel):
    id: UUID | None = None
    name: str | None = None
    gender: Gender | None = None
    birth_date: RangeDTO[date] | None = None
    parent_id: UUID | None = None
    relationship_type: ParentRelationshipType | None = None
    marriage_id: UUID | None = None
    tree_id: UUID | None = None


class FilterPersonQuery(BaseModel):
    pagination: PaginationParams
    filters: PersonFilterDTO | None = None
    sort: SortParams[PersonSortField]
