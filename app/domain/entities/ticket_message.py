from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.exceptions.common_exceptions import UnExpectedIdException


@dataclass
class TicketMessage:
    """
    A single message in a helpdesk ticket conversation.
    """

    ticket_id: UUID
    author_user_id: UUID
    body: str
    id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def safe_id(self) -> UUID:
        if self.id is None:
            raise UnExpectedIdException(
                detail=[f"ticket message ticket_id is {self.ticket_id}"]
            )
        return self.id
