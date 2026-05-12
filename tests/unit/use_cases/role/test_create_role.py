from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.dto.role.role_create_dto import (
    RoleCreateDTO,
    RoleCreateMapper,
)
from app.application.use_cases.role.create_role_use_case import CreateRoleUseCase
from app.domain.entities.role import Role


@pytest.mark.asyncio
async def test_create_role(mock_uow):
    dto = RoleCreateDTO(name="adasdasda", permission_ids=[1, 2])

    perm_1 = MagicMock()
    perm_1.id = 1
    perm_1.safe_id = 1

    perm_2 = MagicMock()
    perm_2.id = 2
    perm_2.safe_id = 2

    mock_uow.permissions.get_or_raise = AsyncMock(side_effect=[perm_1, perm_2])

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
    mock_uow.permissions.get_or_raise.assert_any_await(permission_id=1)
    mock_uow.permissions.get_or_raise.assert_any_await(permission_id=2)

    mock_uow.roles.create.assert_awaited_once()

    assert mock_uow.roles.create.await_args is not None
    created_role_arg = mock_uow.roles.create.await_args.args[0]
    assert created_role_arg.name == dto.name
    assert created_role_arg.permission_ids == dto.permission_ids

    mapper_mock.assert_called_once_with(created_role)


@pytest.mark.asyncio
async def test_create_role_without_permissions(mock_uow):
    dto = RoleCreateDTO(name="admin", permission_ids=[])
    created_role = Role(id=10, name="admin", permission_ids=[])

    mock_uow.roles.create = AsyncMock(return_value=created_role)
    mock_uow.roles.is_role_name_duplicated = AsyncMock(return_value=False)

    expected_result = MagicMock()

    # patch mapper
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
