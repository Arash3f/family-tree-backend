from collections.abc import Mapping
from datetime import date
from enum import Enum
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.marriage import Marriage
from app.domain.repositories.marriage_repository import MarriageRepository
from app.domain.shared.dto.marriage_filter_dto import (
    FilterMarriageDTO,
    MarriageSortField,
)
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.infrastructure.database.models.marriage_model import MarriageModel
from app.infrastructure.database.utils.pagination_and_sort import paginate_and_sort
from app.infrastructure.database.utils.range_filter import apply_range_filter


class SQLMarriageRepository(MarriageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, marriage: Marriage) -> Marriage:
        model = self._to_model(marriage)

        self.session.add(model)

        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def end(self, marriage_id: int, divorced_at: date) -> None:
        stmt = (
            update(MarriageModel)
            .where(MarriageModel.id == marriage_id)
            .values(divorced_at=divorced_at)
        )

        await self.session.execute(stmt)

    async def get_list_by_filter(
        self, query: FilterMarriageDTO
    ) -> PaginatedResult[Marriage]:
        stmt = select(MarriageModel)

        filters = query.filters

        if filters:
            if filters.husband_id is not None:
                stmt = stmt.where(MarriageModel.husband_id == filters.husband_id)

            if filters.wife_id is not None:
                stmt = stmt.where(MarriageModel.wife_id == filters.wife_id)

            if filters.id:
                stmt = stmt.where(MarriageModel.id >= filters.id)

            stmt = apply_range_filter(
                stmt, MarriageModel.married_at, filters.married_at
            )

            stmt = apply_range_filter(
                stmt, MarriageModel.divorced_at, filters.divorced_at
            )

        SORTABLE_COLUMNS: Mapping[Enum, Any] = {
            MarriageSortField.ID: MarriageModel.id,
            MarriageSortField.MARRIAD_AT: MarriageModel.married_at,
            MarriageSortField.DIVORCED_AT: MarriageModel.divorced_at,
        }
        result = await paginate_and_sort(
            model=MarriageModel,
            page=query.pagination.page,
            page_size=query.pagination.page_size,
            session=self.session,
            sort_by=query.sort.sort_by,
            sort_order=query.sort.sort_order,
            sortable_columns=SORTABLE_COLUMNS,
            stmt=stmt,
        )

        marriages = [self._to_entity(m) for m in result.items]

        return PaginatedResult[Marriage](
            items=marriages,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def get(self, marriage_id: int) -> Marriage:
        model = await self.session.get(MarriageModel, marriage_id)

        if not model:
            raise ValueError("Marriage not found")

        return self._to_entity(model)

    async def delete(self, marriage_id: int) -> None:
        stmt = delete(MarriageModel).where(MarriageModel.id == marriage_id)

        await self.session.execute(stmt)

    async def update(self, marriage: Marriage) -> Marriage:
        model = await self.session.get(MarriageModel, marriage.id)

        if not model:
            raise ValueError("Marriage not found")

        model.husband_id = marriage.husband_id
        model.wife_id = marriage.wife_id
        model.married_at = marriage.married_at
        model.divorced_at = marriage.divorced_at

        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    def _to_entity(self, model: MarriageModel) -> Marriage:
        return Marriage(
            id=model.id,
            husband_id=model.husband_id,
            wife_id=model.wife_id,
            married_at=model.married_at,
            divorced_at=model.divorced_at,
        )

    def _to_model(self, entity: Marriage) -> MarriageModel:
        return MarriageModel(
            id=entity.id,
            husband_id=entity.husband_id,
            wife_id=entity.wife_id,
            married_at=entity.married_at,
            divorced_at=entity.divorced_at,
        )
