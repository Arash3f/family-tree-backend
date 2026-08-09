from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dto.ticket.ticket_response_dto import (
    TicketMessageResponseDTO,
    message_to_dto,
)
from app.domain.entities.ticket_message import TicketMessage


class TicketAddMessageDTO(BaseModel):
    ticket_id: UUID
    author_user_id: UUID
    body: str = Field(min_length=1)
    can_manage: bool = False


class TicketAddMessageMapper(BaseModel):
    @staticmethod
    def to_response(message: TicketMessage) -> TicketMessageResponseDTO:
        return message_to_dto(message)
