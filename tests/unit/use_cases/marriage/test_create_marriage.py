from uuid import UUID
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
from app.domain.entities.person import Gender
from app.domain.exceptions.person_exceptions import PersonNotFoundException
from app.domain.exceptions.marriage_exceptions import (
    UnderageMarriageException,
)


@pytest.mark.asyncio
async def test_create_marriage_success(mock_uow):
    dto = MarriageCreateDTO(
        spouse_a_id=UUID(int=1),
        spouse_b_id=UUID(int=2),
        married_at=date(2020, 1, 1),
    )

    husband = MagicMock()
    husband.gender = Gender.MALE
    husband.id = UUID(int=1)
    husband.safe_id = UUID(int=1)
    husband.tree_id = UUID(int=7)
    husband.name = "Ali"
    husband.age = MagicMock(return_value=30)

    wife = MagicMock()
    wife.gender = Gender.FEMALE
    wife.id = UUID(int=2)
    wife.safe_id = UUID(int=2)
    wife.tree_id = UUID(int=7)
    wife.name = "Sara"
    wife.age = MagicMock(return_value=28)

    mock_uow.persons.get_in_tree_or_raise = AsyncMock(side_effect=[husband, wife])

    created_marriage = MagicMock(spec=Marriage)
    created_marriage.spouse_a_id = UUID(int=1)
    created_marriage.spouse_b_id = UUID(int=2)
    mock_uow.marriages.create = AsyncMock(return_value=created_marriage)

    expected_response = MarriageCreateResponseDTO(
        id=UUID(int=10),
        spouse_a_id=UUID(int=1),
        spouse_b_id=UUID(int=2),
        divorced_at=None,
        married_at=date(2020, 1, 1),
    )

    rules = MagicMock()
    sync_service = MagicMock()

    with patch.object(
        MarriageCreateMapper, "to_response", return_value=expected_response
    ) as mapper_mock:
        use_case = CreateMarriageUseCase(
            mock_uow, marriage_rules_service=rules, sync_service=sync_service
        )
        result = await use_case.execute(dto, tree_id=UUID(int=7))

    assert result == expected_response

    rules.validate_marriage.assert_called_once_with(
        spouse_a=husband, spouse_b=wife, marriage_date=dto.married_at
    )
    sync_service.upsert_spouse.assert_called_once_with(UUID(int=1), UUID(int=2))

    mock_uow.persons.get_in_tree_or_raise.assert_any_await(
        person_id=dto.spouse_a_id, tree_id=UUID(int=7)
    )
    mock_uow.persons.get_in_tree_or_raise.assert_any_await(
        person_id=dto.spouse_b_id, tree_id=UUID(int=7)
    )

    mock_uow.marriages.create.assert_awaited_once()

    assert mock_uow.marriages.create.await_args is not None
    created_entity = mock_uow.marriages.create.await_args.args[0]
    assert isinstance(created_entity, Marriage)
    assert created_entity.tree_id == UUID(int=7)
    assert created_entity.spouse_a_id == dto.spouse_a_id
    assert created_entity.spouse_b_id == dto.spouse_b_id
    assert created_entity.married_at == dto.married_at

    mock_uow.commit.assert_awaited_once()

    mapper_mock.assert_called_once_with(marriage=created_marriage)


@pytest.mark.asyncio
async def test_create_marriage_raises_if_husband_not_found(mock_uow):
    dto = MarriageCreateDTO(
        spouse_a_id=UUID(int=1),
        spouse_b_id=UUID(int=2),
        married_at=date(2020, 1, 1),
    )

    mock_uow.persons.get_in_tree_or_raise = AsyncMock(
        side_effect=PersonNotFoundException()
    )

    use_case = CreateMarriageUseCase(
        mock_uow, marriage_rules_service=MagicMock(), sync_service=MagicMock()
    )

    with pytest.raises(PersonNotFoundException):
        await use_case.execute(dto, tree_id=UUID(int=7))

    mock_uow.marriages.create.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_marriage_raises_if_wife_not_found(mock_uow):
    dto = MarriageCreateDTO(
        spouse_a_id=UUID(int=1),
        spouse_b_id=UUID(int=2),
        married_at=date(2020, 1, 1),
    )

    mock_uow.persons.get_in_tree_or_raise = AsyncMock(
        side_effect=[MagicMock(), PersonNotFoundException()]
    )

    use_case = CreateMarriageUseCase(
        mock_uow, marriage_rules_service=MagicMock(), sync_service=MagicMock()
    )

    with pytest.raises(PersonNotFoundException):
        await use_case.execute(dto, tree_id=UUID(int=7))

    mock_uow.marriages.create.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_marriage_raises_if_rules_fail(mock_uow):
    dto = MarriageCreateDTO(
        spouse_a_id=UUID(int=1),
        spouse_b_id=UUID(int=2),
        married_at=date(2020, 1, 1),
    )

    mock_uow.persons.get_in_tree_or_raise = AsyncMock(
        side_effect=[MagicMock(tree_id=UUID(int=7)), MagicMock(tree_id=UUID(int=7))]
    )
    rules = MagicMock()
    rules.validate_marriage.side_effect = UnderageMarriageException()

    use_case = CreateMarriageUseCase(
        mock_uow, marriage_rules_service=rules, sync_service=MagicMock()
    )

    with pytest.raises(UnderageMarriageException):
        await use_case.execute(dto, tree_id=UUID(int=7))

    mock_uow.marriages.create.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
