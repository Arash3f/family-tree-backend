from datetime import date
from enum import Enum

from pydantic import BaseModel

from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.range_dto import RangeDTO
from app.domain.shared.dto.sorter_dto import SortParams


class MarriageSortField(str, Enum):
    ID = "id"
    MARRIAD_AT = "married_at"
    DIVORCED_AT = "divorced_at"


class MarriageFilterDataDTO(BaseModel):
    id: int | None = None
    husband_id: int | None = None
    wife_id: int | None = None
    married_at: RangeDTO[date] | None = None
    divorced_at: RangeDTO[date] | None = None


class FilterMarriageDTO(BaseModel):
    pagination: PaginationParams
    filters: MarriageFilterDataDTO | None = None
    sort: SortParams[MarriageSortField]
