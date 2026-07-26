from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.shared.dto.marriage_filter_dto import MarriageSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    RangeRequest,
    SortRequestParams,
)


class MarriageModel(BaseModel):
    id: UUID | None
    husband_id: UUID
    wife_id: UUID
    married_at: date
    divorced_at: date | None = None


class _MarriageUpdateDateRequest(BaseModel):
    husband_id: UUID | None = None
    wife_id: UUID | None = None
    married_at: date | None = None
    divorced_at: date | None = None


class _MarriageUpdateWhereRequest(BaseModel):
    marriage_id: UUID


class MarriageUpdateRequest(BaseModel):
    data: _MarriageUpdateDateRequest
    where: _MarriageUpdateWhereRequest


class MarriageUpdateResponse(BaseModel):
    id: UUID
    husband_id: UUID
    wife_id: UUID
    married_at: date
    divorced_at: date | None


class MarriageGetResponse(BaseModel):
    id: UUID
    husband_id: UUID
    wife_id: UUID
    married_at: date
    divorced_at: date | None


class MarriageCreateRequest(BaseModel):
    husband_id: UUID
    wife_id: UUID
    married_at: date


class MarriageCreateResponse(BaseModel):
    id: UUID
    husband_id: UUID
    wife_id: UUID
    married_at: date
    divorced_at: date | None


class DivorceRequest(BaseModel):
    marriage_id: UUID
    divorced_at: date


class MarriageFilterRequestData(BaseModel):
    id: UUID | None = None
    husband_id: UUID | None = None
    wife_id: UUID | None = None
    married_at: RangeRequest[date] | None = None
    divorced_at: RangeRequest[date] | None = None


class FilterMarriageRequest(BaseModel):
    pagination: PaginationRequestParams = Field(default_factory=PaginationRequestParams)
    filters: MarriageFilterRequestData | None = None
    sort: SortRequestParams[MarriageSortField] = Field(
        default_factory=lambda: SortRequestParams(
            sort_order=SortOrderField.DESC,
            sort_by=MarriageSortField.ID,
        )
    )
