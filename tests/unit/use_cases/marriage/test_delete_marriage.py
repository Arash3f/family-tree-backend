import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.use_cases.marriage.delete_marriage_use_case import (
    DeleteMarriageUseCase,
)
from app.domain.exceptions.marriage_exceptions import MarriageNotFoundException
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


@pytest.mark.asyncio
async def test_delete_marriage_success(mock_uow):
    dto = IdDTO(id=1)

    marriage = MagicMock()
    marriage.safe_id = 10

    mock_uow.marriages.get_or_raise = AsyncMock(return_value=marriage)

    use_case = DeleteMarriageUseCase(mock_uow)

    result = await use_case.execute(dto)

    assert isinstance(result, ResultDTO)
    assert result.result == "Marriage deleted successfuly"

    mock_uow.marriages.get_or_raise.assert_awaited_once_with(marriage_id=dto.id)
    mock_uow.marriages.delete.assert_awaited_once_with(marriage_id=marriage.safe_id)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_marriage_propagates_exception_from_get_or_raise(mock_uow):
    dto = IdDTO(id=1)

    mock_uow.marriages.get_or_raise = AsyncMock(side_effect=MarriageNotFoundException())

    use_case = DeleteMarriageUseCase(mock_uow)

    # Act / Assert
    with pytest.raises(MarriageNotFoundException):
        await use_case.execute(dto)

    mock_uow.marriages.get_or_raise.assert_awaited_once_with(marriage_id=dto.id)

    mock_uow.marriages.delete.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
