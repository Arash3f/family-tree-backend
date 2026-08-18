from enum import StrEnum


class AccountType(StrEnum):
    FREE = "free"
    PAID = "paid"


FREE_MAX_OWNED_TREES = 1
FREE_MAX_PERSONS_PER_TREE = 10
FREE_MAX_MARRIAGES_PER_TREE = 5
