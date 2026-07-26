from unittest.mock import MagicMock

from app.domain.shared.dto.range_dto import RangeDTO
from app.infrastructure.database.utils.range_filter import apply_range_filter


def test_apply_range_filter_none_returns_stmt():
    stmt = MagicMock()
    assert apply_range_filter(stmt, MagicMock(), None) is stmt
    stmt.where.assert_not_called()


def test_apply_range_filter_min_and_max():
    stmt = MagicMock()
    stmt.where.return_value = stmt
    column = MagicMock()
    column.__ge__ = MagicMock(return_value="ge")
    column.__le__ = MagicMock(return_value="le")

    result: object = apply_range_filter(stmt, column, RangeDTO(min=1, max=10))

    assert result is stmt
    assert stmt.where.call_count == 2
