from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.shared.enums.ticket_category import TicketCategory
from app.domain.shared.enums.ticket_status import TicketStatus


@dataclass
class Ticket:
    """
    Support helpdesk ticket created by a user.
    """

    title: str
    status: TicketStatus
    category: TicketCategory
    created_by_user_id: UUID
    family_tree_id: UUID | None = None
    family_tree_name: str | None = None
    id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def safe_id(self) -> UUID:
        if self.id is None:
            raise UnExpectedIdException(detail=[f"ticket title is {self.title}"])
        return self.id

    def is_closed(self) -> bool:
        return self.status == TicketStatus.CLOSED

    def is_owned_by(self, user_id: UUID) -> bool:
        return self.created_by_user_id == user_id
