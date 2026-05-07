from unittest.mock import MagicMock

from app.application.use_cases.role.delete_role_use_case import DeleteRoleUseCase
from app.domain.exceptions.role_exceptions import RoleNotFoundException
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO
import pytest


@pytest.mark.asyncio
async def test_delete_role_success(mock_uow):
    dto = IdDTO(id=123)

    fake_role = MagicMock()
    fake_role.safe_id = 123
    mock_uow.roles.get_or_raise.return_value = fake_role

    use_case = DeleteRoleUseCase(mock_uow)
    result = await use_case.execute(dto)
    assert result == ResultDTO(result="Role deleted successfuly")

    mock_uow.__aenter__.assert_awaited_once()
    mock_uow.__aexit__.assert_awaited_once()

    mock_uow.roles.get_or_raise.assert_awaited_once_with(role_id=123)
    mock_uow.roles.delete.assert_awaited_once_with(role_id=123)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_role_not_found(mock_uow):
    dto = IdDTO(id=123)

    mock_uow.roles.get_or_raise.side_effect = RoleNotFoundException()

    use_case = DeleteRoleUseCase(mock_uow)

    with pytest.raises(RoleNotFoundException):
        await use_case.execute(dto)

    mock_uow.__aenter__.assert_awaited_once()
    mock_uow.__aexit__.assert_awaited_once()

    mock_uow.roles.get_or_raise.assert_awaited_once_with(role_id=123)
    mock_uow.roles.delete.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
