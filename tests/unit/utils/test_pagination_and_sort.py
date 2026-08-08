from enum import Enum
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, select

from app.domain.shared.dto.sorter_dto import SortOrderField
from app.infrastructure.database.utils.pagination_and_sort import paginate_and_sort
from app.utils.app_exception import AppException

metadata = MetaData()
sample_table = Table("sample", metadata, Column("id", Integer, primary_key=True))


class SortBy(str, Enum):
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
