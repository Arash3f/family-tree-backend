from uuid import UUID
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.dto.person.person_get_dto import PersonGetMapper
from app.application.use_cases.person.get_person_use_case import GetPersonUseCase
from app.domain.exceptions.person_exceptions import PersonNotFoundException
from app.domain.shared.dto.common_dto import IdDTO


def _photo_service():
    service = MagicMock()
    service.presign = AsyncMock(return_value=None)
    return service


@pytest.mark.asyncio
async def test_get_person_success(mock_uow):
    dto = IdDTO(id=UUID(int=1))

    person = MagicMock()
    person.id = UUID(int=1)
    person.photo_object_key = None

    expected_response = MagicMock()

    mock_uow.persons.get_in_tree_or_raise = AsyncMock(return_value=person)

    use_case = GetPersonUseCase(mock_uow, _photo_service())

    with patch.object(
        PersonGetMapper, "to_response", return_value=expected_response
    ) as mapper_mock:
        result = await use_case.execute(dto, tree_id=UUID(int=7))

    assert result is expected_response

    mock_uow.persons.get_in_tree_or_raise.assert_awaited_once_with(
        person_id=UUID(int=1), tree_id=UUID(int=7)
    )
    mapper_mock.assert_called_once_with(person=person, photo_url=None)


@pytest.mark.asyncio
async def test_get_person_propagates_exception(mock_uow):
    dto = IdDTO(id=UUID(int=1))

    mock_uow.persons.get_in_tree_or_raise = AsyncMock(
        side_effect=PersonNotFoundException()
    )

    use_case = GetPersonUseCase(mock_uow, _photo_service())

    with patch.object(PersonGetMapper, "to_response") as mapper_mock:
        with pytest.raises(PersonNotFoundException):
            await use_case.execute(dto, tree_id=UUID(int=7))

    mock_uow.persons.get_in_tree_or_raise.assert_awaited_once_with(
        person_id=UUID(int=1), tree_id=UUID(int=7)
    )
    mapper_mock.assert_not_called()
