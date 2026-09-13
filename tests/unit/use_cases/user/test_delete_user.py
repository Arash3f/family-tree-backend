from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.application.use_cases.user.delete_user_use_case import DeleteUserUseCase
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.domain.shared.dto.common_dto import IdDTO


@pytest.mark.asyncio
async def test_delete_user_success(mock_uow):
    dto = IdDTO(id=UUID(int=1))

    user = MagicMock()
    user.safe_id = UUID(int=1)
    user.is_active = True

    owned_tree = MagicMock()
    owned_tree.safe_id = UUID(int=10)

    mock_uow.users.get_or_raise = AsyncMock(return_value=user)
    mock_uow.users.update = AsyncMock(return_value=user)
    mock_uow.family_trees.list_owned_by_user = AsyncMock(return_value=[owned_tree])
    mock_uow.tree_memberships.delete_all_for_tree = AsyncMock()
    mock_uow.tree_memberships.delete_all_for_user = AsyncMock()
    mock_uow.commit = AsyncMock()

    use_case = DeleteUserUseCase(mock_uow)

    result = await use_case.execute(dto)

    assert result.result == "User deleted successfully"
    assert user.is_active is False

    mock_uow.users.get_or_raise.assert_awaited_once_with(user_id=UUID(int=1))
    mock_uow.users.update.assert_awaited_once_with(user)
    mock_uow.family_trees.list_owned_by_user.assert_awaited_once_with(UUID(int=1))
    mock_uow.tree_memberships.delete_all_for_tree.assert_awaited_once_with(UUID(int=10))
    mock_uow.tree_memberships.delete_all_for_user.assert_awaited_once_with(UUID(int=1))
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_user_propagates_exception(mock_uow):
    dto = IdDTO(id=UUID(int=1))

    mock_uow.users.get_or_raise = AsyncMock(side_effect=UserNotFoundException())
    mock_uow.users.update = AsyncMock()
    mock_uow.commit = AsyncMock()

    use_case = DeleteUserUseCase(mock_uow)

    with pytest.raises(UserNotFoundException):
        await use_case.execute(dto)

    mock_uow.users.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
