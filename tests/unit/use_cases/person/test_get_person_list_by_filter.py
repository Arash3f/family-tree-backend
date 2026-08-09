import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.dto.person.person_get_dto import PersonGetMapper
from app.application.use_cases.person.get_person_list_by_filter_use_case import (
    GetPersonListByFilterUseCase,
)
from app.domain.shared.dto.pagination_dto import PaginatedResult


@pytest.mark.asyncio
async def test_get_person_list_by_filter_success(mock_uow):
    query = MagicMock()

    person = MagicMock()
    person.photo_object_key = None
    page = PaginatedResult(items=[person], total=1, page=1, page_size=10)

    mock_uow.persons.get_list_by_filter = AsyncMock(return_value=page)

    photo_service = MagicMock()
    photo_service.presign = AsyncMock(return_value=None)
    mapped = MagicMock()

    with patch.object(PersonGetMapper, "to_response", return_value=mapped) as mapper:
        use_case = GetPersonListByFilterUseCase(mock_uow, photo_service)
        result = await use_case.execute(query)

    assert result.items == [mapped]
    assert result.total == 1
    assert result.page == 1
    assert result.page_size == 10
    mock_uow.persons.get_list_by_filter.assert_awaited_once_with(query=query)
    mapper.assert_called_once_with(person, photo_url=None)
    photo_service.presign.assert_awaited_once_with(None)
