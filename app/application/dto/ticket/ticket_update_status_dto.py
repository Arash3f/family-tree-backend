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
    current_user_id: UUID
    can_manage: bool = False


class TicketUpdateStatusMapper(BaseModel):
    @staticmethod
    def to_response(
        ticket: Ticket, created_by_can_manage: bool = False
    ) -> TicketSummaryResponseDTO:
        return ticket_to_summary_dto(ticket, created_by_can_manage)
