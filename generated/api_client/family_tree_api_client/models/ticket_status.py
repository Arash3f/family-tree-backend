from enum import Enum


class TicketStatus(str, Enum):
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"
    OPEN = "open"

    def __str__(self) -> str:
        return str(self.value)
