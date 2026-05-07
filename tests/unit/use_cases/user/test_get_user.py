import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.dto.user.user_get_dto import UserGetMapper
from app.application.use_cases.user.get_user_use_case import GetUserUseCase
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.domain.shared.dto.common_dto import IdDTO


@pytest.mark.asyncio
async def test_get_user_success(mock_uow):
    # Arrange
    dto = IdDTO(id=1)

    user = MagicMock(id=1, username="arash")
    expected_response = MagicMock()

    mock_uow.users.get_or_raise = AsyncMock(return_value=user)

    use_case = GetUserUseCase(mock_uow)

    with patch.object(
        UserGetMapper, "to_response", return_value=expected_response
    ) as mapper_mock:
        result = await use_case.execute(dto)

    assert result is expected_response
    mock_uow.users.get_or_raise.assert_awaited_once_with(user_id=1)
    mapper_mock.assert_called_once_with(user=user)


@pytest.mark.asyncio
async def test_get_user_propagates_exception(mock_uow):
    dto = IdDTO(id=1)

    mock_uow.users.get_or_raise = AsyncMock(side_effect=UserNotFoundException())

    use_case = GetUserUseCase(mock_uow)

    with patch.object(UserGetMapper, "to_response") as mapper_mock:
        with pytest.raises(UserNotFoundException):
            await use_case.execute(dto)

    mock_uow.users.get_or_raise.assert_awaited_once_with(user_id=1)
    mapper_mock.assert_not_called()
