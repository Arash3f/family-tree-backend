from app.application.dto.ticket.ticket_create_dto import (
    TicketCreateDTO,
    TicketCreateMapper,
)
from app.application.dto.ticket.ticket_response_dto import TicketDetailResponseDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_message import TicketMessage
from app.domain.shared.enums.ticket_status import TicketStatus


class CreateTicketUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: TicketCreateDTO) -> TicketDetailResponseDTO:
        async with self.uow:
            ticket = Ticket(
                title=dto.title.strip(),
                status=TicketStatus.OPEN,
                created_by_user_id=dto.created_by_user_id,
            )
            ticket = await self.uow.tickets.create(ticket)

            message = TicketMessage(
                ticket_id=ticket.safe_id,
                author_user_id=dto.created_by_user_id,
                body=dto.body.strip(),
            )
            message = await self.uow.ticket_messages.create(message)

            await self.uow.commit()

            return TicketCreateMapper.to_response(ticket, [message])
