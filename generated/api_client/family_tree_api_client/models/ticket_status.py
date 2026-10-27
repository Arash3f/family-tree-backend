from enum import StrEnum


class TicketStatus(StrEnum):
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"
    OPEN = "open"

    def __str__(self) -> str:
        return str(self.value)
