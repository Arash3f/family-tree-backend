from datetime import date

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.application.dto.person.person_create_dto import PersonCreateMapper
from app.application.use_cases.person.create_person_use_case import CreatePersonUseCase
from app.domain.entities.person import Gender
from app.domain.exceptions.person_exceptions import InvalidPersonGenderException


@pytest.mark.asyncio
async def test_create_person_success_with_parents(mock_uow):
    dto = MagicMock()
    dto.name = "Ali"
    dto.gender = Gender.MALE
    dto.birth_date = date(2000, 1, 1)
    dto.father_id = 1
    dto.mother_id = 2

    father = MagicMock()
    father.gender = Gender.MALE

    mother = MagicMock()
    mother.gender = Gender.FEMALE

    created_person = MagicMock()

    mock_uow.persons.get_or_raise = AsyncMock(side_effect=[father, mother])
    mock_uow.persons.create = AsyncMock(return_value=created_person)

    expected_response = MagicMock()

    with patch.object(
        PersonCreateMapper, "to_response", return_value=expected_response
    ) as mapper_mock:
        use_case = CreatePersonUseCase(mock_uow)
        result = await use_case.execute(dto)

    assert result == expected_response

    mock_uow.persons.get_or_raise.assert_any_await(person_id=dto.father_id)
    mock_uow.persons.get_or_raise.assert_any_await(person_id=dto.mother_id)

    mock_uow.persons.create.assert_awaited_once()

    mock_uow.commit.assert_awaited_once()

    mapper_mock.assert_called_once_with(created_person)

    assert mock_uow.persons.create.await_args is not None
    created_entity = mock_uow.persons.create.await_args.args[0]
    assert created_entity.name == "Ali"
    assert created_entity.gender == Gender.MALE
    assert created_entity.father_id == 1
    assert created_entity.mother_id == 2


@pytest.mark.asyncio
async def test_create_person_invalid_father_gender(mock_uow):
    dto = MagicMock()
    dto.name = "Ali"
    dto.gender = Gender.MALE
    dto.birth_date = date(2000, 1, 1)
    dto.father_id = 1
    dto.mother_id = None

    father = MagicMock()
    father.gender = Gender.FEMALE

    mock_uow.persons.get_or_raise = AsyncMock(return_value=father)

    use_case = CreatePersonUseCase(mock_uow)

    with pytest.raises(InvalidPersonGenderException):
        await use_case.execute(dto)

    mock_uow.persons.create.assert_not_called()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_person_invalid_mother_gender(mock_uow):
    dto = MagicMock()
    dto.name = "Sara"
    dto.gender = Gender.FEMALE
    dto.birth_date = date(2000, 1, 1)
    dto.father_id = None
    dto.mother_id = 2

    mother = MagicMock()
    mother.gender = Gender.MALE

    mock_uow.persons.get_or_raise = AsyncMock(return_value=mother)

    use_case = CreatePersonUseCase(mock_uow)

    with pytest.raises(InvalidPersonGenderException):
        await use_case.execute(dto)

    mock_uow.persons.create.assert_not_called()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_person_without_parents(mock_uow):
    dto = MagicMock()
    dto.name = "Ali"
    dto.gender = Gender.MALE
    dto.birth_date = date(2000, 1, 1)
    dto.father_id = None
    dto.mother_id = None

    created_person = MagicMock()

    mock_uow.persons.create = AsyncMock(return_value=created_person)
    mock_uow.commit = AsyncMock()

    expected_response = MagicMock()
    with patch.object(
        PersonCreateMapper, "to_response", return_value=expected_response
    ) as mapper_mock:
        use_case = CreatePersonUseCase(mock_uow)
        result = await use_case.execute(dto)

    assert result == expected_response

    mapper_mock.assert_called_once_with(created_person)

    assert mock_uow.persons.create.await_args is not None
    created_entity = mock_uow.persons.create.await_args.args[0]
    assert created_entity.name == "Ali"
    assert created_entity.gender == Gender.MALE
    assert created_entity.father_id is None
    assert created_entity.mother_id is None

    mock_uow.persons.get_or_raise.assert_not_called()
    mock_uow.persons.create.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()
