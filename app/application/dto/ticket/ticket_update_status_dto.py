from uuid import UUID

from pydantic import BaseModel

from app.application.dto.ticket.ticket_response_dto import (
    TicketSummaryResponseDTO,
    ticket_to_summary_dto,
)
from app.domain.entities.ticket import Ticket
from app.domain.shared.enums.ticket_status import TicketStatus


class TicketUpdateStatusDTO(BaseModel):
    ticket_id: UUID
    status: TicketStatus


class TicketUpdateStatusMapper(BaseModel):
    @staticmethod
    def to_response(ticket: Ticket) -> TicketSummaryResponseDTO:
        return ticket_to_summary_dto(ticket)
