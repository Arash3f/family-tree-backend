from enum import Enum


class AccountType(str, Enum):
    FREE = "free"
    PAID = "paid"

    def __str__(self) -> str:
        return str(self.value)
