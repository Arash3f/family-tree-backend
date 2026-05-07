from datetime import date
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.application.use_cases.marriage.update_marriage_use_case import (
    UpdateMarriageUseCase,
)
from app.application.dto.marriage.marriage_update_dto import (
    MarriageUpdateDTOMapper,
    MarriageUpdateResponseDTO,
)
from app.domain.exceptions.marriage_exceptions import MarriageNotFoundException


@pytest.mark.asyncio
async def test_update_marriage_husband_triggers_validation(mock_uow):
    dto = MagicMock()

    dto.where.marriage_id = 1
    dto.data.model_dump.return_value = {"husband_id": 10}

    marriage = MagicMock()
    marriage.husband_id = 1
    marriage.wife_id = 2
    marriage.married_at = date(2020, 1, 1)

    husband = MagicMock()
    husband.safe_id = 1

    wife = MagicMock()
    wife.safe_id = 2

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)

    mock_uow.persons.get_or_raise = AsyncMock(side_effect=[husband, wife])

    marriage.husband_id = 10
    mock_uow.marriages.update = AsyncMock(return_value=marriage)

    rules_service = MagicMock()

    expected_result = MarriageUpdateResponseDTO(
        id=1,
        wife_id=2,
        husband_id=10,
        married_at=date(2020, 1, 1),
        divorced_at=None,
    )

    with patch.object(
        MarriageUpdateDTOMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = UpdateMarriageUseCase(mock_uow, rules_service)
        result = await use_case.execute(dto)

    # --- Assert ---
    assert result is expected_result
    rules_service.validate_marriage.assert_called_once()

    mapper_mock.assert_called_once_with(marriage=marriage)

    assert mock_uow.marriages.get_or_raise.await_count == 1
    assert mock_uow.persons.get_or_raise.await_count == 2

    husband_call = mock_uow.persons.get_or_raise.await_args_list[0]
    assert husband_call.kwargs == {"person_id": 10}
    husband_call = mock_uow.persons.get_or_raise.await_args_list[1]
    assert husband_call.kwargs == {"person_id": 2}

    mock_uow.marriages.update.assert_awaited_once_with(marriage=marriage)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_marriage_wife_triggers_validation(mock_uow):
    dto = MagicMock()

    dto.where.marriage_id = 1
    dto.data.model_dump.return_value = {"wife_id": 20}

    marriage = MagicMock()
    marriage.husband_id = 1
    marriage.wife_id = 2
    marriage.married_at = date(2020, 1, 1)

    husband = MagicMock()
    husband.safe_id = 1

    wife = MagicMock()
    wife.safe_id = 2

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)

    mock_uow.persons.get_or_raise = AsyncMock(side_effect=[husband, wife])

    marriage.wife_id = 20
    mock_uow.marriages.update = AsyncMock(return_value=marriage)

    rules_service = MagicMock()

    expected_result = MarriageUpdateResponseDTO(
        id=1,
        wife_id=20,
        husband_id=1,
        married_at=date(2020, 1, 1),
        divorced_at=None,
    )

    with patch.object(
        MarriageUpdateDTOMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = UpdateMarriageUseCase(mock_uow, rules_service)
        result = await use_case.execute(dto)

    # --- Assert ---
    assert result is expected_result
    rules_service.validate_marriage.assert_called_once()

    mapper_mock.assert_called_once_with(marriage=marriage)

    assert mock_uow.marriages.get_or_raise.await_count == 1
    assert mock_uow.persons.get_or_raise.await_count == 2

    husband_call = mock_uow.persons.get_or_raise.await_args_list[0]
    assert husband_call.kwargs == {"person_id": 20}
    husband_call = mock_uow.persons.get_or_raise.await_args_list[1]
    assert husband_call.kwargs == {"person_id": 1}

    mock_uow.marriages.update.assert_awaited_once_with(marriage=marriage)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_marriage_divorced_at_without_validation(mock_uow):
    dto = MagicMock()

    dto.where.marriage_id = 1
    dto.data.model_dump.return_value = {"divorced_at": date(2023, 1, 1)}

    marriage = MagicMock()
    marriage.husband_id = 1
    marriage.wife_id = 2
    marriage.married_at = date(2020, 1, 1)

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)

    marriage.divorced_at = date(2023, 1, 1)
    mock_uow.marriages.update = AsyncMock(return_value=marriage)

    rules_service = MagicMock()

    expected_result = MarriageUpdateResponseDTO(
        id=1,
        wife_id=2,
        husband_id=10,
        married_at=date(2020, 1, 1),
        divorced_at=date(2023, 1, 1),
    )

    with patch.object(
        MarriageUpdateDTOMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = UpdateMarriageUseCase(mock_uow, rules_service)
        result = await use_case.execute(dto)

    assert result is expected_result
    mock_uow.marriages.update.assert_awaited_once()

    mapper_mock.assert_called_once_with(marriage=marriage)

    assert mock_uow.marriages.get_or_raise.await_count == 1
    assert mock_uow.persons.get_or_raise.await_count == 0

    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_marriage_married_at_triggers_validation(mock_uow):
    dto = MagicMock()

    dto.where.marriage_id = 1
    dto.data.model_dump.return_value = {"married_at": date(2021, 1, 1)}

    marriage = MagicMock()
    marriage.husband_id = 1
    marriage.wife_id = 2
    marriage.married_at = date(2020, 1, 1)

    husband = MagicMock()
    wife = MagicMock()

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)

    mock_uow.persons.get_or_raise = AsyncMock(side_effect=[husband, wife])

    marriage.married_at = date(2021, 1, 1)
    mock_uow.marriages.update = AsyncMock(return_value=marriage)

    expected_result = MarriageUpdateResponseDTO(
        id=1,
        husband_id=1,
        wife_id=2,
        married_at=date(2021, 1, 1),
        divorced_at=None,
    )

    rules_service = MagicMock()

    with patch.object(
        MarriageUpdateDTOMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = UpdateMarriageUseCase(mock_uow, rules_service)
        result = await use_case.execute(dto)

    # --- Assert ---
    assert result is expected_result
    rules_service.validate_marriage.assert_called_once()

    mapper_mock.assert_called_once_with(marriage=marriage)

    assert mock_uow.marriages.get_or_raise.await_count == 1
    assert mock_uow.persons.get_or_raise.await_count == 2

    husband_call = mock_uow.persons.get_or_raise.await_args_list[0]
    assert husband_call.kwargs == {"person_id": 1}
    husband_call = mock_uow.persons.get_or_raise.await_args_list[1]
    assert husband_call.kwargs == {"person_id": 2}

    mock_uow.marriages.update.assert_awaited_once_with(marriage=marriage)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_marriage_propagates_exception_from_get_or_raise(mock_uow):
    dto = MagicMock()
    dto.where.marriage_id = 1
    dto.data.model_dump.return_value = {}

    mock_uow.marriages.get_or_raise = AsyncMock(side_effect=MarriageNotFoundException())

    rules_service = MagicMock()

    use_case = UpdateMarriageUseCase(mock_uow, rules_service)

    with pytest.raises(MarriageNotFoundException):
        await use_case.execute(dto)

    mock_uow.marriages.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
