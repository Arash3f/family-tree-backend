import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.dto.auth_dto import LoginDTO
from app.application.use_cases.login_user import LoginUserUseCase
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException


@pytest.mark.asyncio
async def test_login_user_success(mock_uow):
    dto = LoginDTO(username="arash", password="1234")

    user = MagicMock()
    user.password_hash = "hashed"
    user.safe_id = 1

    mock_uow.users.get_by_username = AsyncMock(return_value=user)

    password_hasher = MagicMock()
    password_hasher.verify.return_value = True

    token_service = MagicMock()
    token_service.create_access_token.return_value = "access_token"
    token_service.create_refresh_token.return_value = "refresh_token"

    use_case = LoginUserUseCase(mock_uow, password_hasher, token_service)

    result = await use_case.execute(dto)

    assert result.access_token == "access_token"
    assert result.refresh_token == "refresh_token"

    mock_uow.users.get_by_username.assert_awaited_once_with("arash")
    password_hasher.verify.assert_called_once_with("1234", "hashed")
    token_service.create_access_token.assert_called_once_with(1)
    token_service.create_refresh_token.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_login_user_invalid_username(mock_uow):
    dto = LoginDTO(username="arash", password="1234")

    mock_uow.users.get_by_username = AsyncMock(return_value=None)

    password_hasher = MagicMock()
    token_service = MagicMock()

    use_case = LoginUserUseCase(mock_uow, password_hasher, token_service)

    with pytest.raises(InvalidCredentialsException):
        await use_case.execute(dto)

    mock_uow.users.get_by_username.assert_awaited_once_with("arash")

    password_hasher.verify.assert_not_called()
    token_service.create_access_token.assert_not_called()


@pytest.mark.asyncio
async def test_login_user_invalid_password(mock_uow):
    dto = LoginDTO(username="arash", password="wrong")

    user = MagicMock()
    user.password_hash = "hashed"

    mock_uow.users.get_by_username = AsyncMock(return_value=user)

    password_hasher = MagicMock()
    password_hasher.verify.return_value = False

    token_service = MagicMock()

    use_case = LoginUserUseCase(mock_uow, password_hasher, token_service)

    with pytest.raises(InvalidCredentialsException):
        await use_case.execute(dto)

    password_hasher.verify.assert_called_once_with("wrong", "hashed")

    token_service.create_access_token.assert_not_called()
    token_service.create_refresh_token.assert_not_called()
