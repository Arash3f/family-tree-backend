from app.application.dto.ticket.ticket_create_dto import (
    TicketCreateDTO,
    TicketCreateMapper,
)
from app.application.dto.ticket.ticket_response_dto import TicketDetailResponseDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.ticket_support_queue import users_can_manage_tickets
from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.ticket import Ticket
from app.domain.entities.ticket_message import TicketMessage
from app.domain.shared.enums.ticket_status import TicketStatus


class CreateTicketUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(self, dto: TicketCreateDTO) -> TicketDetailResponseDTO:
        async with self.uow:
            family_tree_id = dto.family_tree_id
            if family_tree_id is not None:
                await self.access.require_member(
                    tree_id=family_tree_id,
                    user_id=dto.created_by_user_id,
                )

            ticket = Ticket(
                title=dto.title.strip(),
                status=TicketStatus.OPEN,
                category=dto.category,
                created_by_user_id=dto.created_by_user_id,
                family_tree_id=family_tree_id,
            )
            ticket = await self.uow.tickets.create(ticket)

            message = TicketMessage(
                ticket_id=ticket.safe_id,
                author_user_id=dto.created_by_user_id,
                body=dto.body.strip(),
            )
            message = await self.uow.ticket_messages.create(message)

            flags = await users_can_manage_tickets(self.uow, [dto.created_by_user_id])
            await self.uow.commit()

            return TicketCreateMapper.to_response(
                ticket,
                [message],
                flags.get(dto.created_by_user_id, False),
            )
