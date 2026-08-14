from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.application.dto.role.role_create_dto import (
    RoleCreateDTO,
    RoleCreateMapper,
)
from app.application.use_cases.role.create_role_use_case import CreateRoleUseCase
from app.domain.entities.role import Role
from app.domain.shared.permissions import Permissions


@pytest.mark.asyncio
async def test_create_role(mock_uow):
    dto = RoleCreateDTO(name="adasdasda", permission_ids=[UUID(int=1), UUID(int=2)])

    perm_1 = MagicMock()
    perm_1.id = UUID(int=1)
    perm_1.safe_id = UUID(int=1)
    perm_1.name = Permissions.TICKET_READ

    perm_2 = MagicMock()
    perm_2.id = UUID(int=2)
    perm_2.safe_id = UUID(int=2)
    perm_2.name = Permissions.USER_READ

    mock_uow.permissions.get_or_raise = AsyncMock(side_effect=[perm_1, perm_2])
    mock_uow.permissions.get_by_name = AsyncMock()

    created_role = Role(
        name=dto.name,
        permission_ids=dto.permission_ids,
    )
    mock_uow.roles.create = AsyncMock(return_value=created_role)
    mock_uow.roles.is_role_name_duplicated = AsyncMock(return_value=False)

    expected_result = MagicMock()
    use_case = CreateRoleUseCase(mock_uow)

    with patch.object(
        RoleCreateMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        result = await use_case.execute(dto)

    assert result == expected_result

    assert mock_uow.permissions.get_or_raise.await_count == 2
    mock_uow.permissions.get_or_raise.assert_any_await(permission_id=UUID(int=1))
    mock_uow.permissions.get_or_raise.assert_any_await(permission_id=UUID(int=2))

    mock_uow.roles.create.assert_awaited_once()

    assert mock_uow.roles.create.await_args is not None
    created_role_arg = mock_uow.roles.create.await_args.args[0]
    assert created_role_arg.name == dto.name
    assert created_role_arg.permission_ids == dto.permission_ids

    mapper_mock.assert_called_once_with(created_role)


@pytest.mark.asyncio
async def test_create_role_expands_permission_bundles(mock_uow):
    dto = RoleCreateDTO(
        name="user-admin",
        permission_ids=[UUID(int=1)],
    )

    user_create = MagicMock()
    user_create.safe_id = UUID(int=1)
    user_create.name = Permissions.USER_CREATE

    user_read = MagicMock()
    user_read.safe_id = UUID(int=8)
    user_read.name = Permissions.USER_READ

    role_read = MagicMock()
    role_read.safe_id = UUID(int=9)
    role_read.name = Permissions.ROLE_READ

    mock_uow.permissions.get_or_raise = AsyncMock(return_value=user_create)
    mock_uow.permissions.get_by_name = AsyncMock(
        side_effect=lambda name: {
            Permissions.USER_READ: user_read,
            Permissions.ROLE_READ: role_read,
        }[name]
    )
    mock_uow.roles.is_role_name_duplicated = AsyncMock(return_value=False)

    created_role = Role(
        name=dto.name,
        permission_ids=[UUID(int=1), UUID(int=9), UUID(int=8)],
    )
    mock_uow.roles.create = AsyncMock(return_value=created_role)

    expected_result = MagicMock()
    use_case = CreateRoleUseCase(mock_uow)

    with patch.object(RoleCreateMapper, "to_response", return_value=expected_result):
        await use_case.execute(dto)

    created_role_arg = mock_uow.roles.create.await_args.args[0]
    assert created_role_arg.permission_ids == [UUID(int=1), UUID(int=9), UUID(int=8)]
    assert mock_uow.permissions.get_by_name.await_count == 2


@pytest.mark.asyncio
async def test_create_role_without_permissions(mock_uow):
    dto = RoleCreateDTO(name="admin", permission_ids=[])
    created_role = Role(id=UUID(int=10), name="admin", permission_ids=[])

    mock_uow.roles.create = AsyncMock(return_value=created_role)
    mock_uow.roles.is_role_name_duplicated = AsyncMock(return_value=False)

    expected_result = MagicMock()

    with patch.object(
        RoleCreateMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = CreateRoleUseCase(mock_uow)
        result = await use_case.execute(dto)

    assert mock_uow.permissions.get_or_raise.await_count == 0

    mock_uow.roles.create.assert_awaited_once()

    assert mock_uow.roles.create.await_args is not None
    created_role_arg = mock_uow.roles.create.await_args.args[0]
    assert created_role_arg.name == "admin"
    assert created_role_arg.permission_ids == []

    mock_uow.commit.assert_awaited_once()
    assert mock_uow.permissions.get_or_raise.await_count == 0

    mapper_mock.assert_called_once_with(created_role)

    assert result is expected_result
