from typing import TypeVar

from sqlalchemy import Select
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.domain.shared.dto.range_dto import RangeDTO

T = TypeVar("T")


def apply_range_filter(
    stmt: Select[tuple[T]], column: InstrumentedAttribute, value: RangeDTO | None
) -> Select[tuple[T]]:
    """
    Applies an inclusive range filter (min <= column <= max) to a SQLAlchemy statement.

    Args:
        stmt (Select): The base SQLAlchemy select statement.
        column (InstrumentedAttribute): The SQLAlchemy model column to filter on.
        value (RangeDTO | None): The range object containing optional min/max values.

    Returns:
        Select: The updated statement with range filters applied.

    Example:
        stmt = apply_range_filter(stmt, Person.age, RangeDTO(min=18, max=30))
    """
    if value is None:
        return stmt

    if value.min is not None:
        stmt = stmt.where(column >= value.min)

    if value.max is not None:
        stmt = stmt.where(column <= value.max)

    return stmt
