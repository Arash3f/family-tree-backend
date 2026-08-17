from uuid import UUID

import pytest
from unittest.mock import AsyncMock

from app.application.services.account_limit_service import AccountLimitService
from app.domain.entities.family_tree import FamilyTree
from app.domain.entities.user import User
from app.domain.exceptions.family_tree_exceptions import FreeAccountLimitException
from app.domain.shared.account_type import AccountType


TREE_ID = UUID(int=11)
OWNER_ID = UUID(int=22)


def _owner(*, account_type: AccountType) -> User:
    return User(
        id=OWNER_ID,
        username="owner",
        password_hash="hash",
        account_type=account_type,
    )


def _tree() -> FamilyTree:
    return FamilyTree(id=TREE_ID, name="Tree", owner_user_id=OWNER_ID)


@pytest.mark.asyncio
async def test_paid_owner_can_create_without_limits(mock_uow):
    mock_uow.users.get_for_update = AsyncMock(
        return_value=_owner(account_type=AccountType.PAID)
    )
    service = AccountLimitService()

    await service.assert_can_create_tree(mock_uow, owner_user_id=OWNER_ID)
    await service.assert_can_create_persons(mock_uow, tree_id=TREE_ID, additional=100)
    await service.assert_can_create_marriages(mock_uow, tree_id=TREE_ID, additional=100)

    mock_uow.family_trees.count_owned_by_user.assert_not_awaited()
    mock_uow.persons.count_in_tree.assert_not_awaited()
    mock_uow.marriages.count_in_tree.assert_not_awaited()


@pytest.mark.asyncio
async def test_free_owner_blocked_from_second_tree(mock_uow):
    mock_uow.users.get_for_update = AsyncMock(
        return_value=_owner(account_type=AccountType.FREE)
    )
    mock_uow.family_trees.count_owned_by_user = AsyncMock(return_value=1)
    service = AccountLimitService()

    with pytest.raises(FreeAccountLimitException):
        await service.assert_can_create_tree(mock_uow, owner_user_id=OWNER_ID)


@pytest.mark.asyncio
async def test_free_owner_blocked_from_eleventh_person(mock_uow):
    mock_uow.users.get_for_update = AsyncMock(
        return_value=_owner(account_type=AccountType.FREE)
    )
    mock_uow.family_trees.get_or_raise = AsyncMock(return_value=_tree())
    mock_uow.persons.count_in_tree = AsyncMock(return_value=10)
    service = AccountLimitService()

    with pytest.raises(FreeAccountLimitException):
        await service.assert_can_create_persons(mock_uow, tree_id=TREE_ID, additional=1)


@pytest.mark.asyncio
async def test_free_owner_blocked_from_sixth_marriage(mock_uow):
    mock_uow.users.get_for_update = AsyncMock(
        return_value=_owner(account_type=AccountType.FREE)
    )
    mock_uow.family_trees.get_or_raise = AsyncMock(return_value=_tree())
    mock_uow.marriages.count_in_tree = AsyncMock(return_value=5)
    service = AccountLimitService()

    with pytest.raises(FreeAccountLimitException):
        await service.assert_can_create_marriages(
            mock_uow, tree_id=TREE_ID, additional=1
        )


@pytest.mark.asyncio
async def test_free_owner_allows_person_within_limit(mock_uow):
    mock_uow.users.get_for_update = AsyncMock(
        return_value=_owner(account_type=AccountType.FREE)
    )
    mock_uow.family_trees.get_or_raise = AsyncMock(return_value=_tree())
    mock_uow.persons.count_in_tree = AsyncMock(return_value=9)
    service = AccountLimitService()

    await service.assert_can_create_persons(mock_uow, tree_id=TREE_ID, additional=1)
