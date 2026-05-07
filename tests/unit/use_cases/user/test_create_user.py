from app.application.dto.user.user_create_dto import (
    UserCreateDTO,
    UserCreateMapper,
)
from app.application.use_cases.user.create_user_use_case import CreateUserUseCase
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_create_user_with_role(mock_uow):
    dto = UserCreateDTO(
        username="arash",
        password="secret",
        re_password="secret",
        role_id=1,
    )

    role = MagicMock()
    role.id = 1

    created_user = MagicMock()
    created_user.id = 10
    created_user.username = "arash"
    created_user.role_id = 1

    password_hasher = MagicMock()
    password_hasher.hash.return_value = "hashed_password"

    mock_uow.roles.get_or_raise = AsyncMock(return_value=role)
    mock_uow.users.create = AsyncMock(return_value=created_user)
    mock_uow.commit = AsyncMock()

    expected_response = MagicMock()

    use_case = CreateUserUseCase(mock_uow, password_hasher)

    with patch.object(
        UserCreateMapper, "to_response", return_value=expected_response
    ) as mapper_mock:
        result = await use_case.execute(dto)

    assert result is expected_response

    mock_uow.roles.get_or_raise.assert_awaited_once_with(role_id=1)

    password_hasher.hash.assert_called_once_with("secret")

    mock_uow.users.create.assert_awaited_once()
    args = mock_uow.users.create.await_args
    assert args is not None

    user_arg = args.args[0]

    assert user_arg.username == "arash"
    assert user_arg.role_id == 1
    assert user_arg.password_hash == "hashed_password"

    mock_uow.commit.assert_awaited_once()

    mapper_mock.assert_called_once_with(created_user)


@pytest.mark.asyncio
async def test_create_user_without_role(mock_uow):
    dto = UserCreateDTO(
        username="arash",
        password="secret",
        re_password="secret",
        role_id=None,
    )

    created_user = MagicMock()
    created_user.id = 10
    created_user.username = "arash"
    created_user.role_id = None

    password_hasher = MagicMock()
    password_hasher.hash.return_value = "hashed_password"

    mock_uow.roles.get_or_raise = AsyncMock()
    mock_uow.users.create = AsyncMock(return_value=created_user)
    mock_uow.commit = AsyncMock()

    expected_response = MagicMock()

    use_case = CreateUserUseCase(mock_uow, password_hasher)

    with patch.object(
        UserCreateMapper,
        "to_response",
        return_value=expected_response,
    ) as mapper_mock:
        result = await use_case.execute(dto)

    assert result is expected_response

    mock_uow.roles.get_or_raise.assert_not_awaited()

    password_hasher.hash.assert_called_once_with("secret")

    mock_uow.users.create.assert_awaited_once()

    args = mock_uow.users.create.await_args
    assert args is not None

    user_arg = args.args[0]

    assert user_arg.username == "arash"
    assert user_arg.role_id is None
    assert user_arg.password_hash == "hashed_password"

    mock_uow.commit.assert_awaited_once()

    mapper_mock.assert_called_once_with(created_user)
