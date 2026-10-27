from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.application.use_cases.auth.get_usage import GetMyUsageUseCase
from app.domain.entities.family_tree import FamilyTree
from app.domain.entities.user import User
from app.domain.shared.account_type import AccountType

USER_ID = UUID(int=1)
TREE_A = FamilyTree(id=UUID(int=10), name="A", owner_user_id=USER_ID)
TREE_B = FamilyTree(id=UUID(int=11), name="B", owner_user_id=USER_ID)


def _user(account_type: AccountType, paid_until: date | None = None) -> User:
    return User(
        id=USER_ID,
        username="u",
        password_hash="h",
        account_type=account_type,
        paid_until=paid_until,
    )


def _with_trees(mock_uow, user: User) -> None:
    mock_uow.users.get_or_raise = AsyncMock(return_value=user)
    mock_uow.family_trees.list_owned_by_user = AsyncMock(return_value=[TREE_A, TREE_B])
    counts = {TREE_A.id: (14, 3), TREE_B.id: (2, 0)}
    mock_uow.persons.count_in_tree = AsyncMock(side_effect=lambda t: counts[t][0])
    mock_uow.marriages.count_in_tree = AsyncMock(side_effect=lambda t: counts[t][1])


@pytest.mark.asyncio
async def test_free_account_reports_counts_against_quotas(mock_uow):
    _with_trees(mock_uow, _user(AccountType.FREE))

    usage = await GetMyUsageUseCase(mock_uow).execute(USER_ID)

    assert usage.account_type == "free"
    assert usage.limited is True
    assert usage.days_left is None
    assert usage.owned_trees == 2
    assert [(t.name, t.persons, t.marriages) for t in usage.trees] == [
        ("A", 14, 3),
        ("B", 2, 0),
    ]
    assert usage.free_limits.persons_per_tree == 20


@pytest.mark.asyncio
async def test_paid_account_counts_down_its_days(mock_uow):
    today = datetime.now(UTC).date()
    _with_trees(mock_uow, _user(AccountType.PAID, today + timedelta(days=13)))

    usage = await GetMyUsageUseCase(mock_uow).execute(USER_ID)

    assert usage.account_type == "paid"
    assert usage.limited is False
    # Today and the 13 days after it.
    assert usage.days_left == 14


@pytest.mark.asyncio
async def test_lapsed_paid_account_reads_free(mock_uow):
    _with_trees(mock_uow, _user(AccountType.PAID, date(2000, 1, 1)))

    usage = await GetMyUsageUseCase(mock_uow).execute(USER_ID)

    assert usage.account_type == "free"
    assert usage.limited is True
    assert usage.days_left is None
    assert usage.paid_until == date(2000, 1, 1)
