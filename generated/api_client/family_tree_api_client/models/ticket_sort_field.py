from enum import StrEnum


class TicketSortField(StrEnum):
    CATEGORY = "category"
    CREATED_AT = "created_at"
    ID = "id"
    STATUS = "status"
    TITLE = "title"
    UPDATED_AT = "updated_at"

    def __str__(self) -> str:
        return str(self.value)
