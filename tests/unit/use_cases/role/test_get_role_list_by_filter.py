import pytest
from unittest.mock import MagicMock

from app.application.use_cases.role.get_role_list_by_filter_use_case import (
    GetRoleListByFilterUseCase,
)


@pytest.mark.asyncio
async def test_get_role_list_by_filter(mock_uow):
    query = MagicMock()
    expected = MagicMock()

    mock_uow.roles.get_list_by_filter.return_value = expected

    use_case = GetRoleListByFilterUseCase(mock_uow)

    result = await use_case.execute(query)

    mock_uow.__aenter__.assert_awaited_once()
    mock_uow.__aexit__.assert_awaited_once()

    mock_uow.roles.get_list_by_filter.assert_awaited_once_with(query=query)

    assert result == expected
