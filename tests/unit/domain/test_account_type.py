from datetime import date

import pytest

from app.domain.entities.user import User
from app.domain.shared.account_type import AccountType, effective_account_type

TODAY = date(2026, 10, 27)


@pytest.mark.parametrize(
    ("stored", "paid_until", "expected"),
    [
        (AccountType.FREE, None, AccountType.FREE),
        (AccountType.FREE, date(2030, 1, 1), AccountType.FREE),
        (AccountType.PAID, None, AccountType.PAID),
        (AccountType.PAID, date(2026, 11, 30), AccountType.PAID),
        # The last day is covered in full ...
        (AccountType.PAID, TODAY, AccountType.PAID),
        # ... and the plan lapses the day after it.
        (AccountType.PAID, date(2026, 10, 26), AccountType.FREE),
    ],
)
def test_effective_account_type(stored, paid_until, expected):
    assert effective_account_type(stored, paid_until, TODAY) is expected


def test_user_with_lapsed_paid_plan_is_free():
    user = User(
        username="u",
        password_hash="h",
        account_type=AccountType.PAID,
        paid_until=date(2000, 1, 1),
    )

    assert user.is_free
    assert user.effective_account_type is AccountType.FREE
    # The stored plan is only rewritten by the daily expiry task.
    assert user.account_type is AccountType.PAID


def test_user_with_open_ended_paid_plan_is_not_free():
    user = User(username="u", password_hash="h", account_type=AccountType.PAID)

    assert not user.is_free
