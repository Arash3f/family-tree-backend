from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dto.ticket.ticket_response_dto import (
    TicketDetailResponseDTO,
    ticket_to_detail_dto,
)
from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_message import TicketMessage
from app.domain.shared.enums.ticket_category import TicketCategory


class TicketCreateDTO(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    category: TicketCategory
    created_by_user_id: UUID
    family_tree_id: UUID | None = None


class TicketCreateMapper(BaseModel):
    @staticmethod
    def to_response(
        ticket: Ticket,
        messages: list[TicketMessage],
        created_by_can_manage: bool = False,
    ) -> TicketDetailResponseDTO:
        return ticket_to_detail_dto(ticket, messages, created_by_can_manage)
