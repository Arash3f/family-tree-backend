from uuid import UUID
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.use_cases.person.delete_person_use_case import DeletePersonUseCase
from app.domain.exceptions.person_exceptions import PersonNotFoundException
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


def _photo_service():
    service = MagicMock()
    service.delete_quiet = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_delete_person_success(mock_uow):
    dto = IdDTO(id=UUID(int=1))

    person = MagicMock()
    person.safe_id = UUID(int=10)
    person.photo_object_key = "persons/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jpg"

    mock_uow.persons.get_in_tree_or_raise = AsyncMock(return_value=person)
    photo_service = _photo_service()

    use_case = DeletePersonUseCase(
        mock_uow, photo_service, sync_service=MagicMock()
    )

    result = await use_case.execute(dto, tree_id=UUID(int=7))

    assert isinstance(result, ResultDTO)
    assert result.result == "Person deleted successfully"

    mock_uow.persons.get_in_tree_or_raise.assert_awaited_once_with(
        person_id=UUID(int=1), tree_id=UUID(int=7)
    )
    mock_uow.persons.delete.assert_awaited_once_with(person_id=UUID(int=10))
    mock_uow.commit.assert_awaited_once()
    photo_service.delete_quiet.assert_awaited_once_with(person.photo_object_key)


@pytest.mark.asyncio
async def test_delete_person_propagates_get_exception(mock_uow):
    dto = IdDTO(id=UUID(int=1))

    mock_uow.persons.get_in_tree_or_raise = AsyncMock(side_effect=PersonNotFoundException())
    mock_uow.persons.delete = AsyncMock()
    mock_uow.commit = AsyncMock()

    use_case = DeletePersonUseCase(
        mock_uow, _photo_service(), sync_service=MagicMock()
    )

    with pytest.raises(PersonNotFoundException):
        await use_case.execute(dto, tree_id=UUID(int=7))

    mock_uow.persons.get_in_tree_or_raise.assert_awaited_once_with(
        person_id=UUID(int=1), tree_id=UUID(int=7)
    )
    mock_uow.persons.delete.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
