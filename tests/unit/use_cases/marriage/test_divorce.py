from datetime import date
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.use_cases.marriage.divorce_use_case import DivorceUseCase
from app.application.dto.marriage.divorce_dto import DivorceDTO
from app.domain.exceptions.marriage_exceptions import MarriageNotFoundException
from app.domain.shared.dto.common_dto import ResultDTO


@pytest.mark.asyncio
async def test_divorce_use_case_success(mock_uow):
    dto = DivorceDTO(marriage_id=1, divorced_at=date(2025, 1, 1))

    marriage = MagicMock()
    marriage.safe_id = 10
    marriage.safe_divorced_at = date(2025, 1, 1)

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)

    use_case = DivorceUseCase(mock_uow)

    result = await use_case.execute(dto)

    assert isinstance(result, ResultDTO)
    assert result.result == "Divorce successfuly added"

    mock_uow.marriages.get_or_raise.assert_awaited_once_with(
        marriage_id=dto.marriage_id
    )
    marriage.divorce.assert_called_once_with(divorced_at=dto.divorced_at)
    mock_uow.marriages.end.assert_awaited_once_with(
        marriage_id=marriage.safe_id, divorced_at=marriage.safe_divorced_at
    )
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_divorce_use_case_propagates_exception_from_get_or_raise(mock_uow):
    dto = DivorceDTO(marriage_id=1, divorced_at=date(2025, 1, 1))

    mock_uow.marriages.get_or_raise = AsyncMock(side_effect=MarriageNotFoundException())

    use_case = DivorceUseCase(mock_uow)

    with pytest.raises(MarriageNotFoundException):
        await use_case.execute(dto)
    mock_uow.marriages.get_or_raise.assert_awaited_once_with(
        marriage_id=dto.marriage_id
    )
    mock_uow.marriages.end.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
