from enum import StrEnum


class AccountType(StrEnum):
    FREE = "free"
    PAID = "paid"


# Matches the two starter trees provisioned on self-signup.
FREE_MAX_OWNED_TREES = 2
FREE_MAX_PERSONS_PER_TREE = 20
FREE_MAX_MARRIAGES_PER_TREE = 8
