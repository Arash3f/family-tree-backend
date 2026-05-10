from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.shared.dto.sorter_dto import SortOrderField
from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode

T = TypeVar("T")


class _PaginatedResult(BaseModel, Generic[T]):
    """
    Generic container for paginated query results.
    """

    items: Sequence[T]
    total: int
    page: int
    page_size: int


async def paginate_and_sort(
    sortable_columns: Mapping[Enum, Any],
    sort_by: Enum,
    model: Any,
    stmt: Select[tuple[Any]],
    session: AsyncSession,
    page: int,
    offset: int,
    page_size: int,
    sort_order: SortOrderField,
) -> _PaginatedResult:
    """
    Apply sorting and pagination to a SQLAlchemy async query.

    This utility function enhances a SQLAlchemy `Select` statement by:
        1. Applying dynamic sorting based on allowed sortable columns.
        2. Computing the total number of records efficiently.
        3. Applying offset/limit pagination.
        4. Executing the query and returning a structured paginated result.

    Args:
        sortable_columns (Mapping[Enum, Any]):
            Mapping between allowed sort fields (Enum values) and
            SQLAlchemy model columns.

        sort_by (Enum):
            Field used for sorting. If the field is not found in
            `sortable_columns`, the query falls back to `model.id`.

        model (Any):
            SQLAlchemy model used as a fallback for default sorting.

        stmt (Select):
            Base SQLAlchemy `Select` statement to apply sorting
            and pagination on.

        session (AsyncSession):
            Async SQLAlchemy database session used to execute the query.

        offset (int):
            Requested offset number.

        page (int):
            Requested page number (1-based index).

        page_size (int):
            Number of records per page.

        sort_order (SortOrderField):
            Sorting direction (ASC or DESC).

    Returns:
        _PaginatedResult:
            A paginated result object containing the retrieved items
            and pagination metadata.

    Notes:
        - The total count is calculated using a subquery with the
          ordering removed to improve performance.
        - This function assumes the query returns ORM entities
          compatible with `result.scalars()`.
    """
    # validation page
    if page < 1:
        raise AppException(
            code=ErrorCode.INVALID_PAGE,
            status_code=422,
            detail=["Page must be greater than or equal to 1."],
        )

    if page_size < 1:
        raise AppException(
            code=ErrorCode.INVALID_PAGE_SIZE,
            status_code=422,
            detail=["Page size must be greater than or equal to 1."],
        )

    sort_column = sortable_columns.get(sort_by, model.id)

    # sorting
    if sort_order == SortOrderField.DESC:
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    # total count
    count_stmt = stmt.order_by(None).subquery()
    total = await session.scalar(select(func.count()).select_from(count_stmt))

    # pagination
    stmt = stmt.offset(offset + (page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)

    items = result.unique().scalars().all()

    return _PaginatedResult(
        items=items,
        total=total or 0,
        page=page,
        page_size=page_size,
    )
