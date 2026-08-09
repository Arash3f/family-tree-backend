from datetime import datetime
from enum import Enum
from uuid import UUID

import strawberry

from app.domain.shared.dto.ticket_filter_dto import TicketSortField
from app.domain.shared.enums.ticket_status import TicketStatus as DomainTicketStatus
from app.presentation.graphql.types.common import PaginationInput, SortOrderEnum


@strawberry.enum(name="TicketStatus")
class TicketStatusEnum(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


@strawberry.enum(name="TicketSortBy")
class TicketSortByEnum(Enum):
    ID = "id"
    TITLE = "title"
    STATUS = "status"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.type
class TicketMessageType:
    id: UUID
    ticket_id: UUID
    author_user_id: UUID
    body: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@strawberry.type
class TicketType:
    id: UUID
    title: str
    status: TicketStatusEnum
    created_by_user_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    messages: list[TicketMessageType]


@strawberry.type
class TicketSummaryType:
    id: UUID
    title: str
    status: TicketStatusEnum
    created_by_user_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


@strawberry.type
class TicketPage:
    items: list[TicketSummaryType]
    total: int
    page: int
    page_size: int


@strawberry.input
class TicketCreateInput:
    title: str
    body: str


@strawberry.input
class TicketMessageCreateInput:
    body: str


@strawberry.input
class TicketUpdateStatusInput:
    status: TicketStatusEnum


@strawberry.input
class TicketFilterInput:
    id: UUID | None = None
    title: str | None = None
    status: TicketStatusEnum | None = None
    created_by_user_id: UUID | None = None


@strawberry.input
class TicketListInput:
    pagination: PaginationInput | None = None
    filters: TicketFilterInput | None = None
    sort_order: SortOrderEnum | None = None
    sort_by: TicketSortByEnum | None = None


def to_ticket_status_enum(value: DomainTicketStatus | str) -> TicketStatusEnum:
    raw = value.value if isinstance(value, DomainTicketStatus) else value
    return TicketStatusEnum(raw)


def to_domain_ticket_status(
    value: TicketStatusEnum | DomainTicketStatus,
) -> DomainTicketStatus:
    if isinstance(value, DomainTicketStatus):
        return value
    return DomainTicketStatus(value.value)


def ticket_sort_field(value: TicketSortByEnum | None) -> TicketSortField:
    return TicketSortField((value or TicketSortByEnum.CREATED_AT).value)


def ticket_message_from_mapping(data: dict) -> TicketMessageType:
    return TicketMessageType(
        id=data["id"],
        ticket_id=data["ticket_id"],
        author_user_id=data["author_user_id"],
        body=data["body"],
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


def ticket_from_mapping(data: dict) -> TicketType:
    messages = [ticket_message_from_mapping(m) for m in (data.get("messages") or [])]
    return TicketType(
        id=data["id"],
        title=data["title"],
        status=to_ticket_status_enum(data["status"]),
        created_by_user_id=data["created_by_user_id"],
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        messages=messages,
    )


def ticket_summary_from_mapping(data: dict) -> TicketSummaryType:
    return TicketSummaryType(
        id=data["id"],
        title=data["title"],
        status=to_ticket_status_enum(data["status"]),
        created_by_user_id=data["created_by_user_id"],
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )
