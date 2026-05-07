import pytest

from app.application.dto.role.role_update_dto import (
    _RoleUpdateDataDTO,
    _RoleUpdateWhereDTO,
    RoleUpdateDTO,
    RoleUpdateMapper,
)
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.application.use_cases.role.update_role_use_case import UpdateRoleUseCase


@pytest.mark.asyncio
async def test_update_role_success(mock_uow):
    dto = RoleUpdateDTO(
        where=_RoleUpdateWhereDTO(role_id=1),
        data=_RoleUpdateDataDTO(
            name="super_admin",
            permission_ids=[10, 20],
        ),
    )

    existing_role = MagicMock()
    existing_role.id = 1
    existing_role.name = "admin"
    existing_role.permission_ids = [1, 2]

    perm_10 = MagicMock()
    perm_10.id = 10

    perm_20 = MagicMock()
    perm_20.id = 20

    updated_role = MagicMock()
    updated_role.id = 1
    updated_role.name = "super_admin"
    updated_role.permission_ids = [10, 20]

    mock_uow.roles.get_or_raise = AsyncMock(return_value=existing_role)
    mock_uow.permissions.get_or_raise = AsyncMock(side_effect=[perm_10, perm_20])
    mock_uow.roles.update = AsyncMock(return_value=updated_role)
    mock_uow.commit = AsyncMock()

    expected_result = MagicMock()

    use_case = UpdateRoleUseCase(mock_uow)

    with patch.object(
        RoleUpdateMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        result = await use_case.execute(dto)

    assert result is expected_result

    mock_uow.roles.get_or_raise.assert_awaited_once_with(role_id=1)

    assert mock_uow.permissions.get_or_raise.await_count == 2
    mock_uow.permissions.get_or_raise.assert_has_awaits(
        [
            call(permission_id=10),
            call(permission_id=20),
        ]
    )

    mock_uow.roles.update.assert_awaited_once()
    update_args = mock_uow.roles.update.await_args
    assert update_args is not None

    role_arg = update_args.kwargs["role"]
    assert role_arg is existing_role
    assert role_arg.name == "super_admin"
    assert role_arg.permission_ids == [10, 20]

    mock_uow.commit.assert_awaited_once()
    mapper_mock.assert_called_once_with(role=updated_role)


@pytest.mark.asyncio
async def test_update_role_without_permission_ids(mock_uow):
    dto = RoleUpdateDTO(
        where=_RoleUpdateWhereDTO(role_id=1),
        data=_RoleUpdateDataDTO(name="super_admin", permission_ids=None),
    )

    existing_role = MagicMock()
    existing_role.id = 1
    existing_role.name = "admin"
    existing_role.permission_ids = [1, 2]

    updated_role = MagicMock()
    updated_role.id = 1
    updated_role.name = "super_admin"
    updated_role.permission_ids = [1, 2]

    mock_uow.roles.get_or_raise = AsyncMock(return_value=existing_role)
    mock_uow.permissions.get_or_raise = AsyncMock()
    mock_uow.roles.update = AsyncMock(return_value=updated_role)
    mock_uow.commit = AsyncMock()

    expected_result = MagicMock()

    use_case = UpdateRoleUseCase(mock_uow)

    with patch.object(
        RoleUpdateMapper,
        "to_response",
        return_value=expected_result,
    ) as mapper_mock:
        result = await use_case.execute(dto)

    assert result is expected_result

    mock_uow.roles.get_or_raise.assert_awaited_once_with(role_id=1)
    mock_uow.permissions.get_or_raise.assert_not_awaited()

    mock_uow.roles.update.assert_awaited_once()
    update_args = mock_uow.roles.update.await_args
    assert update_args is not None

    role_arg = update_args.kwargs["role"]
    assert role_arg is existing_role
    assert role_arg.name == "super_admin"
    assert role_arg.permission_ids == [1, 2]

    mock_uow.commit.assert_awaited_once()
    mapper_mock.assert_called_once_with(role=updated_role)


@pytest.mark.asyncio
async def test_update_role_only_permission_ids(mock_uow):
    dto = RoleUpdateDTO(
        where=_RoleUpdateWhereDTO(role_id=1),
        data=_RoleUpdateDataDTO(permission_ids=[10, 20], name=None),
    )

    existing_role = MagicMock()
    existing_role.id = 1
    existing_role.name = "admin"
    existing_role.permission_ids = [1, 2]

    perm_10 = MagicMock(id=10)
    perm_10.id = 10

    perm_20 = MagicMock(id=20)
    perm_20.id = 20

    updated_role = MagicMock()
    updated_role.id = 1
    updated_role.name = "admin"
    updated_role.permission_ids = [10, 20]

    mock_uow.roles.get_or_raise = AsyncMock(return_value=existing_role)
    mock_uow.permissions.get_or_raise = AsyncMock(side_effect=[perm_10, perm_20])
    mock_uow.roles.update = AsyncMock(return_value=updated_role)
    mock_uow.commit = AsyncMock()

    expected_result = MagicMock()

    use_case = UpdateRoleUseCase(mock_uow)

    with patch.object(
        RoleUpdateMapper,
        "to_response",
        return_value=expected_result,
    ) as mapper_mock:
        result = await use_case.execute(dto)

    assert result is expected_result

    mock_uow.roles.get_or_raise.assert_awaited_once_with(role_id=1)
    mock_uow.permissions.get_or_raise.assert_has_awaits(
        [
            call(permission_id=10),
            call(permission_id=20),
        ]
    )

    update_args = mock_uow.roles.update.await_args
    assert update_args is not None

    role_arg = update_args.kwargs["role"]
    assert role_arg.name == "admin"
    assert role_arg.permission_ids == [10, 20]

    mock_uow.commit.assert_awaited_once()
    mapper_mock.assert_called_once_with(role=updated_role)
