from uuid import UUID
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.application.dto.marriage.marriage_get_dto import MarriageGetMapper
from app.application.use_cases.marriage.get_marriage_use_case import GetMarriageUseCase
from app.domain.exceptions.marriage_exceptions import MarriageNotFoundException
from app.domain.shared.dto.common_dto import IdDTO


@pytest.mark.asyncio
async def test_get_marriage_success(mock_uow):
    dto = IdDTO(id=UUID(int=1))

    marriage = MagicMock()
    mock_uow.marriages.get_in_tree_or_raise = AsyncMock(return_value=marriage)

    expected_response = MagicMock()

    use_case = GetMarriageUseCase(mock_uow)
    with patch.object(
        MarriageGetMapper, "to_response", return_value=expected_response
    ) as mapper_mock:
        result = await use_case.execute(dto, tree_id=UUID(int=7))

    assert result is expected_response

    mock_uow.marriages.get_in_tree_or_raise.assert_awaited_once_with(
        marriage_id=UUID(int=1), tree_id=UUID(int=7)
    )
    mapper_mock.assert_called_once_with(marriage=marriage)


@pytest.mark.asyncio
async def test_get_marriage_propagates_exception(mock_uow):
    dto = IdDTO(id=UUID(int=1))

    mock_uow.marriages.get_in_tree_or_raise = AsyncMock(
        side_effect=MarriageNotFoundException()
    )

    use_case = GetMarriageUseCase(mock_uow)

    with patch.object(MarriageGetMapper, "to_response") as mapper_mock:
        with pytest.raises(MarriageNotFoundException):
            await use_case.execute(dto, tree_id=UUID(int=7))

    mock_uow.marriages.get_in_tree_or_raise.assert_awaited_once_with(
        marriage_id=UUID(int=1), tree_id=UUID(int=7)
    )
    mapper_mock.assert_not_called()
