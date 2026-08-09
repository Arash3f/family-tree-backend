from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.shared.dto.sorter_dto import SortOrderField
from app.domain.shared.dto.ticket_filter_dto import TicketSortField
from app.domain.shared.enums.ticket_status import TicketStatus
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)


class TicketMessageModel(BaseModel):
    id: UUID
    ticket_id: UUID
    author_user_id: UUID
    body: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TicketSummaryModel(BaseModel):
    id: UUID
    title: str
    status: TicketStatus
    created_by_user_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TicketDetailModel(BaseModel):
    id: UUID
    title: str
    status: TicketStatus
    created_by_user_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    messages: list[TicketMessageModel] = Field(default_factory=list)


class TicketCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)


class TicketCreateResponse(TicketDetailModel):
    pass


class TicketGetResponse(TicketDetailModel):
    pass


class TicketMessageCreateRequest(BaseModel):
    body: str = Field(min_length=1)


class TicketMessageCreateResponse(TicketMessageModel):
    pass


class TicketUpdateStatusRequest(BaseModel):
    status: TicketStatus


class TicketUpdateStatusResponse(TicketSummaryModel):
    pass


class TicketFilterRequestData(BaseModel):
    id: UUID | None = None
    title: str | None = None
    status: TicketStatus | None = None
    created_by_user_id: UUID | None = None


class FilterTicketRequest(BaseModel):
    pagination: PaginationRequestParams = Field(default_factory=PaginationRequestParams)
    filters: TicketFilterRequestData | None = None
    sort: SortRequestParams[TicketSortField] = Field(
        default_factory=lambda: SortRequestParams(
            sort_order=SortOrderField.DESC,
            sort_by=TicketSortField.CREATED_AT,
        )
    )
