from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.ticket import Ticket
from app.domain.exceptions.ticket_exceptions import TicketNotFoundException
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.ticket_filter_dto import FilterTicketQuery


class TicketRepository(ABC):
    """
    Repository contract for Ticket persistence.
    """

    @abstractmethod
    async def create(self, ticket: Ticket) -> Ticket: ...

    @abstractmethod
    async def get(self, ticket_id: UUID) -> Ticket | None: ...

    @abstractmethod
    async def get_list_by_filter(
        self, query: FilterTicketQuery
    ) -> PaginatedResult[Ticket]: ...

    @abstractmethod
    async def update(self, ticket: Ticket) -> Ticket: ...

    async def get_or_raise(self, ticket_id: UUID) -> Ticket:
        ticket = await self.get(ticket_id=ticket_id)

        if not ticket:
            raise TicketNotFoundException(detail=[f"ticket id is {ticket_id}"])
        return ticket
