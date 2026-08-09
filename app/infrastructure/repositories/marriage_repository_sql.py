from collections.abc import Mapping
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.marriage import Marriage
from app.domain.exceptions.marriage_exceptions import MarriageNotFoundException
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

    async def end(self, marriage_id: UUID, divorced_at: date) -> None:
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
            if filters.tree_id is not None:
                stmt = stmt.where(MarriageModel.tree_id == filters.tree_id)

            if filters.spouse_a_id is not None:
                stmt = stmt.where(MarriageModel.spouse_a_id == filters.spouse_a_id)

            if filters.spouse_b_id is not None:
                stmt = stmt.where(MarriageModel.spouse_b_id == filters.spouse_b_id)

            if filters.id:
                stmt = stmt.where(MarriageModel.id == filters.id)

            stmt = apply_range_filter(
                stmt, MarriageModel.married_at, filters.married_at
            )

            stmt = apply_range_filter(
                stmt, MarriageModel.divorced_at, filters.divorced_at
            )

        SORTABLE_COLUMNS: Mapping[Enum, Any] = {
            MarriageSortField.ID: MarriageModel.id,
            MarriageSortField.MARRIED_AT: MarriageModel.married_at,
            MarriageSortField.DIVORCED_AT: MarriageModel.divorced_at,
        }
        result = await paginate_and_sort(
            model=MarriageModel,
            page=query.pagination.page,
            page_size=query.pagination.page_size,
            session=self.session,
            sort_by=query.sort.sort_by,
            sort_order=query.sort.sort_order,
            offset=query.pagination.offset,
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

    async def get(self, marriage_id: UUID) -> Marriage | None:
        model = await self.session.get(MarriageModel, marriage_id)

        if not model:
            return None

        return self._to_entity(model)

    async def get_by_ids(self, spouse_a_id: UUID, spouse_b_id: UUID) -> Marriage | None:
        stmt = (
            select(MarriageModel)
            .where(
                MarriageModel.spouse_b_id == spouse_b_id,
                MarriageModel.spouse_a_id == spouse_a_id,
            )
            .order_by(MarriageModel.married_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def has_active_for_person(
        self,
        person_id: UUID,
        exclude_marriage_id: UUID | None = None,
    ) -> bool:
        stmt = select(MarriageModel.id).where(
            MarriageModel.divorced_at.is_(None),
            or_(
                MarriageModel.spouse_a_id == person_id,
                MarriageModel.spouse_b_id == person_id,
            ),
        )
        if exclude_marriage_id is not None:
            stmt = stmt.where(MarriageModel.id != exclude_marriage_id)

        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None

    async def exists_for_person(self, person_id: UUID) -> bool:
        stmt = select(MarriageModel.id).where(
            or_(
                MarriageModel.spouse_a_id == person_id,
                MarriageModel.spouse_b_id == person_id,
            )
        )
        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None

    async def delete(self, marriage_id: UUID) -> None:
        stmt = delete(MarriageModel).where(MarriageModel.id == marriage_id)

        await self.session.execute(stmt)

    async def update(self, marriage: Marriage) -> Marriage:
        model = await self.session.get(MarriageModel, marriage.id)

        # Persistence Guard :)
        if not model:
            raise MarriageNotFoundException(detail=[f"marriage id is {marriage.id}"])

        model.tree_id = marriage.tree_id
        model.spouse_a_id = marriage.spouse_a_id
        model.spouse_b_id = marriage.spouse_b_id
        model.married_at = marriage.married_at
        model.divorced_at = marriage.divorced_at

        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    def _to_entity(self, model: MarriageModel) -> Marriage:
        return Marriage(
            id=model.id,
            tree_id=model.tree_id,
            spouse_a_id=model.spouse_a_id,
            spouse_b_id=model.spouse_b_id,
            married_at=model.married_at,
            divorced_at=model.divorced_at,
        )

    def _to_model(self, entity: Marriage) -> MarriageModel:
        return MarriageModel(
            id=entity.id,
            tree_id=entity.tree_id,
            spouse_a_id=entity.spouse_a_id,
            spouse_b_id=entity.spouse_b_id,
            married_at=entity.married_at,
            divorced_at=entity.divorced_at,
        )
