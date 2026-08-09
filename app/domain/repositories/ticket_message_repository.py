from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.ticket_message import TicketMessage


class TicketMessageRepository(ABC):
    """
    Repository contract for TicketMessage persistence.
    """

    @abstractmethod
    async def create(self, message: TicketMessage) -> TicketMessage: ...

    @abstractmethod
    async def get_by_ticket_id(self, ticket_id: UUID) -> list[TicketMessage]: ...
