from app.application.dto.ticket.ticket_response_dto import TicketSummaryResponseDTO
from app.application.dto.ticket.ticket_update_status_dto import (
    TicketUpdateStatusDTO,
    TicketUpdateStatusMapper,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.ticket_support_queue import users_can_manage_tickets
from app.application.services.tree_ticket_access import user_can_manage_tree_ticket
from app.domain.exceptions.ticket_exceptions import TicketAccessDeniedException


class UpdateTicketStatusUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: TicketUpdateStatusDTO) -> TicketSummaryResponseDTO:
        async with self.uow:
            ticket = await self.uow.tickets.get_or_raise(ticket_id=dto.ticket_id)

            can_manage = dto.can_manage or await user_can_manage_tree_ticket(
                self.uow, dto.current_user_id, ticket.family_tree_id
            )
            if not can_manage:
                raise TicketAccessDeniedException(
                    detail=[f"ticket id is {dto.ticket_id}"]
                )

            ticket.status = dto.status
            ticket = await self.uow.tickets.update(ticket)
            flags = await users_can_manage_tickets(
                self.uow, [ticket.created_by_user_id]
            )
            await self.uow.commit()
            return TicketUpdateStatusMapper.to_response(
                ticket, flags.get(ticket.created_by_user_id, False)
            )
