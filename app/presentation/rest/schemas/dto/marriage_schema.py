from datetime import date

from pydantic import BaseModel

from app.domain.shared.dto.marriage_filter_dto import MarriageSortField
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    RangeRequest,
    SortRequestParams,
)


class MarriageModel(BaseModel):
    id: int | None
    husband_id: int
    wife_id: int
    married_at: date
    divorced_at: date | None = None


class _MarriageUpdateDateRequest(BaseModel):
    husband_id: int | None
    wife_id: int | None
    married_at: date | None
    divorced_at: date | None


class _MarriageUpdateWhereRequest(BaseModel):
    marriage_id: int


class MarriageUpdateRequest(BaseModel):
    data: _MarriageUpdateDateRequest
    where: _MarriageUpdateWhereRequest


class MarriageUpdateResponse(BaseModel):
    id: int
    husband_id: int
    wife_id: int
    married_at: date
    divorced_at: date | None


class MarriageGetResponse(BaseModel):
    id: int
    husband_id: int
    wife_id: int
    married_at: date
    divorced_at: date | None


class MarriageCreateRequest(BaseModel):
    husband_id: int
    wife_id: int
    married_at: date


class MarriageCreateResponse(BaseModel):
    id: int
    husband_id: int
    wife_id: int
    married_at: date
    divorced_at: date | None


class DivorceRequest(BaseModel):
    marriage_id: int
    divorced_at: date


class MarriageFilterRequestData(BaseModel):
    id: int | None = None
    husband_id: int | None = None
    wife_id: int | None = None
    married_at: RangeRequest[date] | None = None
    divorced_at: RangeRequest[date] | None = None


class FilterMarriageRequest(BaseModel):
    pagination: PaginationRequestParams
    filters: MarriageFilterRequestData
    sort: SortRequestParams[MarriageSortField]
