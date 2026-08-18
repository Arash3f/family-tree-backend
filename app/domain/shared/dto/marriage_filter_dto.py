from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.range_dto import RangeDTO
from app.domain.shared.dto.sorter_dto import SortParams


class MarriageSortField(StrEnum):
    ID = "id"
    MARRIED_AT = "married_at"
    DIVORCED_AT = "divorced_at"


class MarriageFilterDataDTO(BaseModel):
    id: UUID | None = None
    spouse_a_id: UUID | None = None
    spouse_b_id: UUID | None = None
    married_at: RangeDTO[date] | None = None
    divorced_at: RangeDTO[date] | None = None
    tree_id: UUID | None = None


class FilterMarriageDTO(BaseModel):
    pagination: PaginationParams
    filters: MarriageFilterDataDTO | None = None
    sort: SortParams[MarriageSortField]
