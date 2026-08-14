from app.application.dto.ticket.ticket_list_dto import TicketListDTO
from app.application.dto.ticket.ticket_response_dto import (
    TicketSummaryResponseDTO,
    ticket_to_summary_dto,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.ticket_support_queue import users_can_manage_tickets
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.ticket_filter_dto import TicketFilterDTO


class GetTicketListByFilterUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self, dto: TicketListDTO
    ) -> PaginatedResult[TicketSummaryResponseDTO]:
        async with self.uow:
            query = dto.query
            filters = query.filters or TicketFilterDTO()

            if not dto.can_manage:
                filters = filters.model_copy(
                    update={"created_by_user_id": dto.current_user_id}
                )

            scoped_query = query.model_copy(update={"filters": filters})
            result = await self.uow.tickets.get_list_by_filter(query=scoped_query)
            flags = await users_can_manage_tickets(
                self.uow, [ticket.created_by_user_id for ticket in result.items]
            )

            return PaginatedResult[TicketSummaryResponseDTO](
                items=[
                    ticket_to_summary_dto(
                        ticket, flags.get(ticket.created_by_user_id, False)
                    )
                    for ticket in result.items
                ],
                total=result.total,
                page=result.page,
                page_size=result.page_size,
            )
