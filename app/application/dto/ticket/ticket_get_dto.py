from uuid import UUID

from pydantic import BaseModel

from app.application.dto.ticket.ticket_response_dto import (
    TicketDetailResponseDTO,
    ticket_to_detail_dto,
)
from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_message import TicketMessage


class TicketGetDTO(BaseModel):
    ticket_id: UUID
    current_user_id: UUID
    can_manage: bool = False


class TicketGetMapper(BaseModel):
    @staticmethod
    def to_response(
        ticket: Ticket, messages: list[TicketMessage]
    ) -> TicketDetailResponseDTO:
        return ticket_to_detail_dto(ticket, messages)
