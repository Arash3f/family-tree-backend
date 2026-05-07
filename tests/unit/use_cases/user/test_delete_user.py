import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases.user.delete_user_use_case import DeleteUserUseCase
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.domain.shared.dto.common_dto import IdDTO


@pytest.mark.asyncio
async def test_delete_user_success(mock_uow):
    dto = IdDTO(id=1)

    user = MagicMock()
    user.safe_id = 1

    mock_uow.users.get_or_raise = AsyncMock(return_value=user)
    mock_uow.users.delete = AsyncMock()
    mock_uow.commit = AsyncMock()

    use_case = DeleteUserUseCase(mock_uow)

    result = await use_case.execute(dto)

    assert result.result == "User deleted successfuly"

    mock_uow.users.get_or_raise.assert_awaited_once_with(user_id=1)
    mock_uow.users.delete.assert_awaited_once_with(user_id=1)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_user_propagates_exception(mock_uow):
    dto = IdDTO(id=1)

    mock_uow.users.get_or_raise = AsyncMock(side_effect=UserNotFoundException())
    mock_uow.users.delete = AsyncMock()
    mock_uow.commit = AsyncMock()

    use_case = DeleteUserUseCase(mock_uow)

    with pytest.raises(UserNotFoundException):
        await use_case.execute(dto)

    mock_uow.users.delete.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
