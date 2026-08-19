from app.application.dto.ticket.ticket_add_message_dto import (
    TicketAddMessageDTO,
    TicketAddMessageMapper,
)
from app.application.dto.ticket.ticket_response_dto import TicketMessageResponseDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_ticket_access import user_can_manage_tree_ticket
from app.domain.entities.ticket_message import TicketMessage
from app.domain.exceptions.ticket_exceptions import (
    TicketAccessDeniedException,
    TicketClosedException,
)


class AddTicketMessageUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: TicketAddMessageDTO) -> TicketMessageResponseDTO:
        async with self.uow:
            ticket = await self.uow.tickets.get_or_raise(ticket_id=dto.ticket_id)

            can_manage = dto.can_manage or await user_can_manage_tree_ticket(
                self.uow, dto.author_user_id, ticket.family_tree_id
            )
            if not can_manage and not ticket.is_owned_by(dto.author_user_id):
                raise TicketAccessDeniedException(
                    detail=[f"ticket id is {dto.ticket_id}"]
                )

            if ticket.is_closed():
                raise TicketClosedException(detail=[f"ticket id is {dto.ticket_id}"])

            message = TicketMessage(
                ticket_id=ticket.safe_id,
                author_user_id=dto.author_user_id,
                body=dto.body.strip(),
            )
            message = await self.uow.ticket_messages.create(message)
            await self.uow.commit()

            return TicketAddMessageMapper.to_response(message)
