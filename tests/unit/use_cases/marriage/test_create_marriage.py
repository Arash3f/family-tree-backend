import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from app.application.use_cases.marriage.create_marriage_use_case import (
    CreateMarriageUseCase,
)
from app.application.dto.marriage.marriage_create_dto import (
    MarriageCreateDTO,
    MarriageCreateMapper,
    MarriageCreateResponseDTO,
)
from app.domain.entities.marriage import Marriage
from app.domain.exceptions.person_exceptions import PersonNotFoundException


@pytest.mark.asyncio
async def test_create_marriage_success(mock_uow):
    dto = MarriageCreateDTO(
        husband_id=1,
        wife_id=2,
        married_at=date(2020, 1, 1),
    )

    created_marriage = MagicMock(spec=Marriage)
    mock_uow.marriages.create = AsyncMock(return_value=created_marriage)

    expected_response = MarriageCreateResponseDTO(
        id=10,
        husband_id=1,
        wife_id=2,
        divorced_at=None,
        married_at=date(2020, 1, 1),
    )

    with patch.object(
        MarriageCreateMapper, "to_response", return_value=expected_response
    ) as mapper_mock:
        use_case = CreateMarriageUseCase(mock_uow)
        result = await use_case.execute(dto)

    assert result == expected_response

    mock_uow.persons.get_or_raise.assert_any_await(person_id=dto.husband_id)
    mock_uow.persons.get_or_raise.assert_any_await(person_id=dto.wife_id)

    mock_uow.marriages.create.assert_awaited_once()

    assert mock_uow.marriages.create.await_args is not None
    created_entity = mock_uow.marriages.create.await_args.args[0]
    assert isinstance(created_entity, Marriage)
    assert created_entity.husband_id == dto.husband_id
    assert created_entity.wife_id == dto.wife_id
    assert created_entity.married_at == dto.married_at

    mock_uow.commit.assert_awaited_once()

    mapper_mock.assert_called_once_with(marriage=created_marriage)


@pytest.mark.asyncio
async def test_create_marriage_raises_if_husband_not_found(mock_uow):
    dto = MarriageCreateDTO(
        husband_id=1,
        wife_id=2,
        married_at=date(2020, 1, 1),
    )

    mock_uow.persons.get_or_raise = AsyncMock(side_effect=PersonNotFoundException())

    use_case = CreateMarriageUseCase(mock_uow)

    with pytest.raises(PersonNotFoundException):
        await use_case.execute(dto)

    mock_uow.marriages.create.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_marriage_raises_if_wife_not_found(mock_uow):
    dto = MarriageCreateDTO(
        husband_id=1,
        wife_id=2,
        married_at=date(2020, 1, 1),
    )

    mock_uow.persons.get_or_raise = AsyncMock(
        side_effect=[MagicMock(), PersonNotFoundException()]
    )

    use_case = CreateMarriageUseCase(mock_uow)

    with pytest.raises(PersonNotFoundException):
        await use_case.execute(dto)

    mock_uow.marriages.create.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
