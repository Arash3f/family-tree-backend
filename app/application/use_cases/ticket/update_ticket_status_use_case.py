from app.application.dto.ticket.ticket_response_dto import TicketSummaryResponseDTO
from app.application.dto.ticket.ticket_update_status_dto import (
    TicketUpdateStatusDTO,
    TicketUpdateStatusMapper,
)
from app.application.interfaces.unit_of_work import UnitOfWork


class UpdateTicketStatusUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: TicketUpdateStatusDTO) -> TicketSummaryResponseDTO:
        async with self.uow:
            ticket = await self.uow.tickets.get_or_raise(ticket_id=dto.ticket_id)
            ticket.status = dto.status
            ticket = await self.uow.tickets.update(ticket)
            await self.uow.commit()
            return TicketUpdateStatusMapper.to_response(ticket)
