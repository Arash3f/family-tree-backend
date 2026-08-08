from uuid import UUID
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

    dto.where.marriage_id = UUID(int=1)
    dto.data.model_dump.return_value = {"husband_id": UUID(int=10)}

    marriage = MagicMock()
    marriage.husband_id = UUID(int=1)
    marriage.wife_id = UUID(int=2)
    marriage.married_at = date(2020, 1, 1)
    marriage.divorced_at = None
    marriage.safe_id = UUID(int=1)

    husband = MagicMock()
    husband.safe_id = UUID(int=1)

    wife = MagicMock()
    wife.safe_id = UUID(int=2)

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)

    mock_uow.persons.get_or_raise = AsyncMock(side_effect=[husband, wife])

    marriage.husband_id = UUID(int=10)
    mock_uow.marriages.update = AsyncMock(return_value=marriage)

    rules_service = MagicMock()

    expected_result = MarriageUpdateResponseDTO(
        id=UUID(int=1),
        wife_id=UUID(int=2),
        husband_id=UUID(int=10),
        married_at=date(2020, 1, 1),
        divorced_at=None,
    )

    with patch.object(
        MarriageUpdateDTOMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = UpdateMarriageUseCase(
            mock_uow, rules_service, sync_service=MagicMock()
        )
        result = await use_case.execute(dto)

    # --- Assert ---
    assert result is expected_result
    rules_service.validate_marriage.assert_called_once()

    mapper_mock.assert_called_once_with(marriage=marriage)

    assert mock_uow.marriages.get_or_raise.await_count == 1
    assert mock_uow.persons.get_or_raise.await_count == 2

    husband_call = mock_uow.persons.get_or_raise.await_args_list[0]
    assert husband_call.kwargs == {"person_id": UUID(int=10)}
    husband_call = mock_uow.persons.get_or_raise.await_args_list[1]
    assert husband_call.kwargs == {"person_id": UUID(int=2)}

    mock_uow.marriages.update.assert_awaited_once_with(marriage=marriage)
    mock_uow.commit.assert_awaited_once()
    mock_uow.marriages.has_active_for_person.assert_awaited()


@pytest.mark.asyncio
async def test_update_marriage_wife_triggers_validation(mock_uow):
    dto = MagicMock()

    dto.where.marriage_id = UUID(int=1)
    dto.data.model_dump.return_value = {"wife_id": UUID(int=20)}

    marriage = MagicMock()
    marriage.husband_id = UUID(int=1)
    marriage.wife_id = UUID(int=2)
    marriage.married_at = date(2020, 1, 1)
    marriage.divorced_at = None
    marriage.safe_id = UUID(int=1)

    husband = MagicMock()
    husband.safe_id = UUID(int=1)

    wife = MagicMock()
    wife.safe_id = UUID(int=2)

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)

    mock_uow.persons.get_or_raise = AsyncMock(side_effect=[husband, wife])

    marriage.wife_id = UUID(int=20)
    mock_uow.marriages.update = AsyncMock(return_value=marriage)

    rules_service = MagicMock()

    expected_result = MarriageUpdateResponseDTO(
        id=UUID(int=1),
        wife_id=UUID(int=20),
        husband_id=UUID(int=1),
        married_at=date(2020, 1, 1),
        divorced_at=None,
    )

    with patch.object(
        MarriageUpdateDTOMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = UpdateMarriageUseCase(
            mock_uow, rules_service, sync_service=MagicMock()
        )
        result = await use_case.execute(dto)

    # --- Assert ---
    assert result is expected_result
    rules_service.validate_marriage.assert_called_once()

    mapper_mock.assert_called_once_with(marriage=marriage)

    assert mock_uow.marriages.get_or_raise.await_count == 1
    assert mock_uow.persons.get_or_raise.await_count == 2

    husband_call = mock_uow.persons.get_or_raise.await_args_list[0]
    assert husband_call.kwargs == {"person_id": UUID(int=20)}
    husband_call = mock_uow.persons.get_or_raise.await_args_list[1]
    assert husband_call.kwargs == {"person_id": UUID(int=1)}

    mock_uow.marriages.update.assert_awaited_once_with(marriage=marriage)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_marriage_divorced_at_without_validation(mock_uow):
    dto = MagicMock()

    dto.where.marriage_id = UUID(int=1)
    dto.data.model_dump.return_value = {"divorced_at": date(2023, 1, 1)}

    marriage = MagicMock()
    marriage.husband_id = UUID(int=1)
    marriage.wife_id = UUID(int=2)
    marriage.married_at = date(2020, 1, 1)
    marriage.divorced_at = None
    marriage.safe_id = UUID(int=1)

    def _divorce(divorced_at):
        marriage.divorced_at = divorced_at

    marriage.divorce.side_effect = _divorce

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)
    mock_uow.marriages.update = AsyncMock(return_value=marriage)

    rules_service = MagicMock()
    sync_service = MagicMock()

    expected_result = MarriageUpdateResponseDTO(
        id=UUID(int=1),
        wife_id=UUID(int=2),
        husband_id=UUID(int=1),
        married_at=date(2020, 1, 1),
        divorced_at=date(2023, 1, 1),
    )

    with patch.object(
        MarriageUpdateDTOMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = UpdateMarriageUseCase(
            mock_uow, rules_service, sync_service=sync_service
        )
        result = await use_case.execute(dto)

    assert result is expected_result
    marriage.divorce.assert_called_once_with(date(2023, 1, 1))
    sync_service.remove_spouse.assert_called_once_with(UUID(int=1), UUID(int=2))
    mock_uow.marriages.update.assert_awaited_once()

    mapper_mock.assert_called_once_with(marriage=marriage)

    assert mock_uow.marriages.get_or_raise.await_count == 1
    assert mock_uow.persons.get_or_raise.await_count == 0

    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_marriage_married_at_triggers_validation(mock_uow):
    dto = MagicMock()

    dto.where.marriage_id = UUID(int=1)
    dto.data.model_dump.return_value = {"married_at": date(2021, 1, 1)}

    marriage = MagicMock()
    marriage.husband_id = UUID(int=1)
    marriage.wife_id = UUID(int=2)
    marriage.married_at = date(2020, 1, 1)
    marriage.divorced_at = None
    marriage.safe_id = UUID(int=1)

    husband = MagicMock()
    wife = MagicMock()

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)

    mock_uow.persons.get_or_raise = AsyncMock(side_effect=[husband, wife])

    marriage.married_at = date(2021, 1, 1)
    mock_uow.marriages.update = AsyncMock(return_value=marriage)

    expected_result = MarriageUpdateResponseDTO(
        id=UUID(int=1),
        husband_id=UUID(int=1),
        wife_id=UUID(int=2),
        married_at=date(2021, 1, 1),
        divorced_at=None,
    )

    rules_service = MagicMock()

    with patch.object(
        MarriageUpdateDTOMapper, "to_response", return_value=expected_result
    ) as mapper_mock:
        use_case = UpdateMarriageUseCase(
            mock_uow, rules_service, sync_service=MagicMock()
        )
        result = await use_case.execute(dto)

    # --- Assert ---
    assert result is expected_result
    rules_service.validate_marriage.assert_called_once()

    mapper_mock.assert_called_once_with(marriage=marriage)

    assert mock_uow.marriages.get_or_raise.await_count == 1
    assert mock_uow.persons.get_or_raise.await_count == 2

    husband_call = mock_uow.persons.get_or_raise.await_args_list[0]
    assert husband_call.kwargs == {"person_id": UUID(int=1)}
    husband_call = mock_uow.persons.get_or_raise.await_args_list[1]
    assert husband_call.kwargs == {"person_id": UUID(int=2)}

    mock_uow.marriages.update.assert_awaited_once_with(marriage=marriage)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_divorced_marriage_spouses_does_not_sync_spouse_edge(mock_uow):
    dto = MagicMock()

    dto.where.marriage_id = UUID(int=1)
    dto.data.model_dump.return_value = {"husband_id": UUID(int=10)}

    marriage = MagicMock()
    marriage.husband_id = UUID(int=1)
    marriage.wife_id = UUID(int=2)
    marriage.married_at = date(2020, 1, 1)
    marriage.divorced_at = date(2023, 1, 1)
    marriage.safe_id = UUID(int=1)

    husband = MagicMock()
    husband.safe_id = UUID(int=10)
    wife = MagicMock()
    wife.safe_id = UUID(int=2)

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)
    mock_uow.persons.get_or_raise = AsyncMock(side_effect=[husband, wife])

    marriage.husband_id = UUID(int=10)
    mock_uow.marriages.update = AsyncMock(return_value=marriage)

    rules_service = MagicMock()
    sync_service = MagicMock()

    expected_result = MarriageUpdateResponseDTO(
        id=UUID(int=1),
        wife_id=UUID(int=2),
        husband_id=UUID(int=10),
        married_at=date(2020, 1, 1),
        divorced_at=date(2023, 1, 1),
    )

    with patch.object(
        MarriageUpdateDTOMapper, "to_response", return_value=expected_result
    ):
        use_case = UpdateMarriageUseCase(
            mock_uow, rules_service, sync_service=sync_service
        )
        result = await use_case.execute(dto)

    assert result is expected_result
    sync_service.replace_spouse.assert_not_called()
    sync_service.upsert_spouse.assert_not_called()
    sync_service.remove_spouse.assert_not_called()
    mock_uow.marriages.has_active_for_person.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_marriage_propagates_exception_from_get_or_raise(mock_uow):
    dto = MagicMock()
    dto.where.marriage_id = UUID(int=1)
    dto.data.model_dump.return_value = {}

    mock_uow.marriages.get_or_raise = AsyncMock(side_effect=MarriageNotFoundException())

    rules_service = MagicMock()

    use_case = UpdateMarriageUseCase(mock_uow, rules_service, sync_service=MagicMock())

    with pytest.raises(MarriageNotFoundException):
        await use_case.execute(dto)

    mock_uow.marriages.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
