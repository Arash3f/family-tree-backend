from enum import Enum


class TicketCategory(str, Enum):
    ACCOUNT = "account"
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"
    OTHER = "other"
    TECHNICAL = "technical"

    def __str__(self) -> str:
        return str(self.value)
