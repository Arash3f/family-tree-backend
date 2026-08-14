from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_message import TicketMessage
from app.domain.shared.enums.ticket_category import TicketCategory
from app.domain.shared.enums.ticket_status import TicketStatus


class TicketMessageResponseDTO(BaseModel):
    id: UUID
    ticket_id: UUID
    author_user_id: UUID
    body: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TicketDetailResponseDTO(BaseModel):
    id: UUID
    title: str
    status: TicketStatus
    category: TicketCategory
    created_by_user_id: UUID
    created_by_can_manage: bool = False
    family_tree_id: UUID | None = None
    family_tree_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    messages: list[TicketMessageResponseDTO] = Field(default_factory=list)


class TicketSummaryResponseDTO(BaseModel):
    id: UUID
    title: str
    status: TicketStatus
    category: TicketCategory
    created_by_user_id: UUID
    created_by_can_manage: bool = False
    family_tree_id: UUID | None = None
    family_tree_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


def message_to_dto(message: TicketMessage) -> TicketMessageResponseDTO:
    return TicketMessageResponseDTO(
        id=message.safe_id,
        ticket_id=message.ticket_id,
        author_user_id=message.author_user_id,
        body=message.body,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


def ticket_to_detail_dto(
    ticket: Ticket,
    messages: list[TicketMessage],
    created_by_can_manage: bool = False,
) -> TicketDetailResponseDTO:
    return TicketDetailResponseDTO(
        id=ticket.safe_id,
        title=ticket.title,
        status=ticket.status,
        category=ticket.category,
        created_by_user_id=ticket.created_by_user_id,
        created_by_can_manage=created_by_can_manage,
        family_tree_id=ticket.family_tree_id,
        family_tree_name=ticket.family_tree_name,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        messages=[message_to_dto(m) for m in messages],
    )


def ticket_to_summary_dto(
    ticket: Ticket, created_by_can_manage: bool = False
) -> TicketSummaryResponseDTO:
    return TicketSummaryResponseDTO(
        id=ticket.safe_id,
        title=ticket.title,
        status=ticket.status,
        category=ticket.category,
        created_by_user_id=ticket.created_by_user_id,
        created_by_can_manage=created_by_can_manage,
        family_tree_id=ticket.family_tree_id,
        family_tree_name=ticket.family_tree_name,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )
