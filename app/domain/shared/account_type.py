from datetime import UTC, date, datetime
from enum import StrEnum


class AccountType(StrEnum):
    FREE = "free"
    PAID = "paid"


# Matches the two starter trees provisioned on self-signup.
FREE_MAX_OWNED_TREES = 2
FREE_MAX_PERSONS_PER_TREE = 20
FREE_MAX_MARRIAGES_PER_TREE = 8


def effective_account_type(
    account_type: AccountType,
    paid_until: date | None,
    today: date | None = None,
) -> AccountType:
    """
    The plan in force on `today` (the current UTC day by default).

    A paid plan covers its `paid_until` day in full and lapses the day after;
    without a `paid_until` it never lapses.
    """
    if account_type is not AccountType.PAID or paid_until is None:
        return account_type
    if paid_until < (today or datetime.now(UTC).date()):
        return AccountType.FREE
    return AccountType.PAID
