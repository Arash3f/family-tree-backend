import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.use_cases.person.delete_person_use_case import DeletePersonUseCase
from app.domain.exceptions.person_exceptions import PersonNotFoundException
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


@pytest.mark.asyncio
async def test_delete_person_success(mock_uow):
    dto = IdDTO(id=1)

    person = MagicMock()
    person.safe_id = 10

    mock_uow.persons.get_or_raise = AsyncMock(return_value=person)

    use_case = DeletePersonUseCase(mock_uow)

    result = await use_case.execute(dto)

    assert isinstance(result, ResultDTO)
    assert result.result == "Person deleted successfuly"

    mock_uow.persons.get_or_raise.assert_awaited_once_with(person_id=1)
    mock_uow.persons.delete.assert_awaited_once_with(person_id=10)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_person_propagates_get_exception(mock_uow):
    dto = IdDTO(id=1)

    mock_uow.persons.get_or_raise = AsyncMock(side_effect=PersonNotFoundException())
    mock_uow.persons.delete = AsyncMock()
    mock_uow.commit = AsyncMock()

    use_case = DeletePersonUseCase(mock_uow)

    with pytest.raises(PersonNotFoundException):
        await use_case.execute(dto)

    mock_uow.persons.get_or_raise.assert_awaited_once_with(person_id=1)
    mock_uow.persons.delete.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
