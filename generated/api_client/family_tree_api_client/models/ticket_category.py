from enum import StrEnum


class TicketCategory(StrEnum):
    ACCOUNT = "account"
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"
    OTHER = "other"
    TECHNICAL = "technical"
    UPGRADE_REQUEST = "upgrade_request"

    def __str__(self) -> str:
        return str(self.value)
