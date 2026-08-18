from enum import StrEnum


class TicketCategory(StrEnum):
    GENERAL = "general"
    ACCOUNT = "account"
    TECHNICAL = "technical"
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    OTHER = "other"
