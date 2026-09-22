from enum import StrEnum
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, select

from app.domain.shared.dto.pagination_dto import MAX_GET_ALL_SIZE, MAX_PAGE_SIZE
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.infrastructure.database.utils.pagination_and_sort import paginate_and_sort
from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode

metadata = MetaData()
sample_table = Table("sample", metadata, Column("id", Integer, primary_key=True))


class SortBy(StrEnum):
    ID = "id"


@pytest.mark.asyncio
async def test_paginate_and_sort_invalid_page():
    with pytest.raises(AppException):
        await paginate_and_sort(
            {},
            SortBy.ID,
            MagicMock(),
            select(sample_table),
            MagicMock(),
            page=0,
            offset=0,
            page_size=10,
            sort_order=SortOrderField.ASC,
        )


@pytest.mark.asyncio
async def test_paginate_and_sort_invalid_page_size():
    with pytest.raises(AppException):
        await paginate_and_sort(
            {},
            SortBy.ID,
            MagicMock(),
            select(sample_table),
            MagicMock(),
            page=1,
            offset=0,
            page_size=0,
            sort_order=SortOrderField.ASC,
        )


@pytest.mark.asyncio
async def test_paginate_and_sort_rejects_page_size_above_cap():
    """The database layer is the last line of defence against huge reads."""
    with pytest.raises(AppException) as exc_info:
        await paginate_and_sort(
            {},
            SortBy.ID,
            MagicMock(),
            select(sample_table),
            MagicMock(),
            page=1,
            offset=0,
            page_size=MAX_PAGE_SIZE + 1,
            sort_order=SortOrderField.ASC,
        )

    assert exc_info.value.code == ErrorCode.INVALID_PAGE_SIZE


@pytest.mark.asyncio
async def test_paginate_and_sort_rejects_negative_offset():
    with pytest.raises(AppException):
        await paginate_and_sort(
            {},
            SortBy.ID,
            MagicMock(),
            select(sample_table),
            MagicMock(),
            page=1,
            offset=-5,
            page_size=10,
            sort_order=SortOrderField.ASC,
        )


@pytest.mark.asyncio
async def test_paginate_and_sort_success():
    session = MagicMock()
    session.scalar = AsyncMock(return_value=2)
    result = MagicMock()
    result.unique.return_value.scalars.return_value.all.return_value = ["a", "b"]
    session.execute = AsyncMock(return_value=result)

    model = MagicMock()
    model.id = sample_table.c.id

    page = await paginate_and_sort(
        {SortBy.ID: sample_table.c.id},
        SortBy.ID,
        model,
        select(sample_table),
        session,
        page=1,
        offset=0,
        page_size=10,
        sort_order=SortOrderField.DESC,
    )

    assert page.items == ["a", "b"]
    assert page.total == 2
    assert page.page == 1
    assert page.page_size == 10


@pytest.mark.asyncio
async def test_paginate_and_sort_get_all_skips_offset_limit():
    session = MagicMock()
    session.scalar = AsyncMock(return_value=3)
    result = MagicMock()
    result.unique.return_value.scalars.return_value.all.return_value = ["a", "b", "c"]
    session.execute = AsyncMock(return_value=result)

    model = MagicMock()
    model.id = sample_table.c.id

    page = await paginate_and_sort(
        {SortBy.ID: sample_table.c.id},
        SortBy.ID,
        model,
        select(sample_table),
        session,
        page=2,
        offset=10,
        page_size=10,
        sort_order=SortOrderField.ASC,
        get_all=True,
    )

    assert page.items == ["a", "b", "c"]
    assert page.total == 3
    assert page.page == 1
    assert page.page_size == 3
    executed_stmt = session.execute.await_args.args[0]
    assert executed_stmt._limit_clause is None
    assert executed_stmt._offset_clause is None


@pytest.mark.asyncio
async def test_paginate_and_sort_get_all_rejects_oversized_result():
    session = MagicMock()
    session.scalar = AsyncMock(return_value=MAX_GET_ALL_SIZE + 1)

    model = MagicMock()
    model.id = sample_table.c.id

    with pytest.raises(AppException) as exc_info:
        await paginate_and_sort(
            {SortBy.ID: sample_table.c.id},
            SortBy.ID,
            model,
            select(sample_table),
            session,
            page=1,
            offset=0,
            page_size=1,
            sort_order=SortOrderField.ASC,
            get_all=True,
        )

    assert exc_info.value.code == ErrorCode.INVALID_PAGE_SIZE


@pytest.mark.asyncio
async def test_paginate_and_sort_tie_breaks_on_id_for_stable_pages():
    """Non-unique sort keys must still produce stable OFFSET pages."""
    session = MagicMock()
    session.scalar = AsyncMock(return_value=0)
    result = MagicMock()
    result.unique.return_value.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=result)

    name_col = Column("name", Integer)
    model = MagicMock()
    model.id = sample_table.c.id

    class SortByName(StrEnum):
        NAME = "name"

    base = select(sample_table)
    await paginate_and_sort(
        {SortByName.NAME: name_col},
        SortByName.NAME,
        model,
        base,
        session,
        page=2,
        offset=0,
        page_size=10,
        sort_order=SortOrderField.ASC,
    )

    executed_stmt = session.execute.await_args.args[0]
    order_by = list(executed_stmt._order_by_clauses)
    assert len(order_by) == 2
    assert "name" in str(order_by[0])
    assert "id" in str(order_by[1])
