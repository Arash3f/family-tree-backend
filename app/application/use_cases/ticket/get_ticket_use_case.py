from app.application.dto.ticket.ticket_get_dto import TicketGetDTO, TicketGetMapper
from app.application.dto.ticket.ticket_response_dto import TicketDetailResponseDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.ticket_exceptions import TicketAccessDeniedException


class GetTicketUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: TicketGetDTO) -> TicketDetailResponseDTO:
        async with self.uow:
            ticket = await self.uow.tickets.get_or_raise(ticket_id=dto.ticket_id)

            if not dto.can_manage and not ticket.is_owned_by(dto.current_user_id):
                raise TicketAccessDeniedException(
                    detail=[f"ticket id is {dto.ticket_id}"]
                )

            messages = await self.uow.ticket_messages.get_by_ticket_id(
                ticket_id=ticket.safe_id
            )

            return TicketGetMapper.to_response(ticket, messages)
