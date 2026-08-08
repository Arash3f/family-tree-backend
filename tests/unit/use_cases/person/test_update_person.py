from uuid import UUID
from datetime import date

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.dto.person.person_update_dto import PersonUpdateMapper
from app.application.use_cases.person.update_person_use_case import UpdatePersonUseCase
from app.domain.entities.person import Gender


@pytest.mark.asyncio
async def test_update_person_success(mock_uow):
    dto = MagicMock()
    dto.where.person_id = UUID(int=1)
    dto.data.model_dump.return_value = {
        "name": "Arash",
        "birth_date": date(2000, 1, 1),
        "father_id": UUID(int=10),
        "mother_id": UUID(int=20),
    }

    person = MagicMock()
    person.safe_id = UUID(int=1)
    person.father_id = None
    person.mother_id = None
    person.gender = Gender.MALE

    father = MagicMock()
    father.safe_id = UUID(int=10)
    father.gender = Gender.MALE
    mother = MagicMock()
    mother.safe_id = UUID(int=20)
    mother.gender = Gender.FEMALE

    expected_result = MagicMock()
    sync_service = MagicMock()

    mock_uow.persons.get_or_raise = AsyncMock(side_effect=[person, father, mother])
    mock_uow.persons.update = AsyncMock(return_value=person)

    with patch.object(
        PersonUpdateMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = UpdatePersonUseCase(mock_uow, sync_service=sync_service)
        result = await use_case.execute(dto)

    # --- Assert ---
    assert result is expected_result
    assert mock_uow.persons.get_or_raise.await_count == 3

    father_call = mock_uow.persons.get_or_raise.await_args_list[1]
    mother_call = mock_uow.persons.get_or_raise.await_args_list[2]
    assert father_call.kwargs == {"person_id": UUID(int=10)}
    assert mother_call.kwargs == {"person_id": UUID(int=20)}

    person.set_father.assert_called_once_with(UUID(int=10))
    person.set_mother.assert_called_once_with(UUID(int=20))
    mock_uow.persons.update.assert_awaited_once_with(person=person)
    mock_uow.commit.assert_awaited_once()
    mapper_mock.assert_called_once_with(person=person)
