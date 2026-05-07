import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.dto.user.user_update_dto import (
    _UserUpdateDataDTO,
    _UserUpdateWhereDTO,
    UserUpdateDTO,
    UserUpdateMapper,
)
from app.application.use_cases.user.update_user_use_case import UpdateUserUseCase


@pytest.mark.asyncio
async def test_update_user_full_update(mock_uow):
    dto = UserUpdateDTO(
        where=_UserUpdateWhereDTO(user_id=1),
        data=_UserUpdateDataDTO(
            username="new_username",
            role_id=2,
            password="1234",
            re_password="1234",
        ),
    )

    existing_user = MagicMock(
        id=1,
        username="old",
        role_id=1,
        password_hash="old_hash",
    )

    role = MagicMock()
    role.safe_id = 2

    updated_user = MagicMock()

    mock_uow.users.get_or_raise = AsyncMock(return_value=existing_user)
    mock_uow.roles.get_or_raise = AsyncMock(return_value=role)
    mock_uow.users.update = AsyncMock(return_value=updated_user)
    mock_uow.commit = AsyncMock()

    password_hasher = MagicMock()
    password_hasher.hash.return_value = "new_hash"

    expected_response = MagicMock()

    use_case = UpdateUserUseCase(mock_uow, password_hasher)

    with patch.object(
        UserUpdateMapper,
        "to_response",
        return_value=expected_response,
    ) as mapper_mock:
        result = await use_case.execute(dto)

    assert result is expected_response

    mock_uow.users.get_or_raise.assert_awaited_once_with(user_id=1)
    mock_uow.roles.get_or_raise.assert_awaited_once_with(role_id=2)

    password_hasher.hash.assert_called_once_with("1234")

    mock_uow.users.update.assert_awaited_once()
    args = mock_uow.users.update.await_args
    assert args is not None

    user_arg = args.kwargs["user"]

    assert user_arg.username == "new_username"
    assert user_arg.role_id == 2
    assert user_arg.password_hash == "new_hash"

    mock_uow.commit.assert_awaited_once()
    mapper_mock.assert_called_once_with(user=updated_user)


@pytest.mark.asyncio
async def test_update_user_only_role(mock_uow):
    dto = UserUpdateDTO(
        where=_UserUpdateWhereDTO(user_id=1),
        data=_UserUpdateDataDTO(
            role_id=5,
            password=None,
            re_password=None,
            username=None,
        ),
    )

    existing_user = MagicMock(role_id=1)
    role = MagicMock()
    role.safe_id = 5

    mock_uow.users.get_or_raise = AsyncMock(return_value=existing_user)
    mock_uow.roles.get_or_raise = AsyncMock(return_value=role)
    mock_uow.users.update = AsyncMock(return_value=existing_user)
    mock_uow.commit = AsyncMock()

    password_hasher = MagicMock()

    use_case = UpdateUserUseCase(mock_uow, password_hasher)

    with patch.object(UserUpdateMapper, "to_response", return_value=MagicMock()):
        await use_case.execute(dto)

    password_hasher.hash.assert_not_called()
    assert existing_user.role_id == 5
