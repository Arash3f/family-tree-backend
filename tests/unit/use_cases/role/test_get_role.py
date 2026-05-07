import pytest
from unittest.mock import MagicMock, patch
from app.application.dto.role.role_get_dto import RoleGetMapper
from app.application.use_cases.role.get_role_use_case import GetRoleUseCase
from app.domain.exceptions.role_exceptions import RoleNotFoundException
from app.domain.shared.dto.common_dto import IdDTO


@pytest.mark.asyncio
async def test_get_role_success(mock_uow):
    dto = IdDTO(id=123)

    fake_role = MagicMock()
    mock_uow.roles.get_or_raise.return_value = fake_role

    expected_result = MagicMock()

    with patch.object(
        RoleGetMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = GetRoleUseCase(mock_uow)
        result = await use_case.execute(dto)

    mock_uow.__aenter__.assert_awaited_once()
    mock_uow.__aexit__.assert_awaited_once()

    mock_uow.roles.get_or_raise.assert_awaited_once_with(role_id=123)

    mapper_mock.assert_called_once_with(role=fake_role)

    assert result is expected_result


@pytest.mark.asyncio
async def test_get_role_not_found(mock_uow):
    dto = IdDTO(id=999)

    mock_uow.roles.get_or_raise.side_effect = RoleNotFoundException()

    use_case = GetRoleUseCase(mock_uow)

    with pytest.raises(RoleNotFoundException):
        await use_case.execute(dto)

    mock_uow.__aenter__.assert_awaited_once()
    mock_uow.__aexit__.assert_awaited_once()

    mock_uow.roles.get_or_raise.assert_awaited_once_with(role_id=999)
