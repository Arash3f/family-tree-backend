from enum import StrEnum


class AccountType(StrEnum):
    FREE = "free"
    PAID = "paid"

    def __str__(self) -> str:
        return str(self.value)
