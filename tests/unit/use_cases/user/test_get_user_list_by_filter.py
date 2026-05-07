import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases.user.get_user_list_by_filter_use_case import (
    GetUserListByFilterUseCase,
)


@pytest.mark.asyncio
async def test_get_user_list_by_filter_success(mock_uow):
    query = MagicMock()

    expected_result = MagicMock()

    mock_uow.users.get_list_by_filter = AsyncMock(return_value=expected_result)

    use_case = GetUserListByFilterUseCase(mock_uow)

    result = await use_case.execute(query)

    assert result is expected_result

    mock_uow.users.get_list_by_filter.assert_awaited_once_with(query=query)
