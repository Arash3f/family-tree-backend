from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dto.ticket.ticket_response_dto import (
    TicketDetailResponseDTO,
    ticket_to_detail_dto,
)
from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_message import TicketMessage


class TicketCreateDTO(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    created_by_user_id: UUID


class TicketCreateMapper(BaseModel):
    @staticmethod
    def to_response(
        ticket: Ticket, messages: list[TicketMessage]
    ) -> TicketDetailResponseDTO:
        return ticket_to_detail_dto(ticket, messages)
