from collections.abc import Mapping
from enum import Enum
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.person import Gender, Person
from app.domain.repositories.person_repository import PersonRepository
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.person_filter_dto import FilterPersonQuery, PersonSortField
from app.infrastructure.database.models.person_model import PersonModel
from app.infrastructure.database.utils.pagination_and_sort import paginate_and_sort
from app.infrastructure.database.utils.range_filter import apply_range_filter


class SQLPersonRepository(PersonRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, person: Person) -> Person:
        model = self._to_model(person)

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def get(self, person_id: int) -> Person | None:
        stmt = select(PersonModel).where(PersonModel.id == person_id)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_by_name(
        self, name: str, father_id: int | None, mother_id: int | None
    ) -> Person | None:
        stmt = select(PersonModel).where(
            PersonModel.name == name,
            PersonModel.father_id == father_id,
            PersonModel.mother_id == mother_id,
        )
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_list_by_filter(
        self, query: FilterPersonQuery
    ) -> PaginatedResult[Person]:
        stmt = select(PersonModel)
        filters = query.filters

        if filters:
            if filters.name:
                stmt = stmt.where(PersonModel.name.ilike(f"%{filters.name}%"))

            if filters.gender:
                stmt = stmt.where(PersonModel.gender == filters.gender)

            if filters.father_id:
                stmt = stmt.where(PersonModel.father_id == filters.father_id)

            if filters.mother_id:
                stmt = stmt.where(PersonModel.mother_id == filters.mother_id)

            stmt = apply_range_filter(stmt, PersonModel.birth_date, filters.birth_date)

        SORTABLE_COLUMNS: Mapping[Enum, Any] = {
            PersonSortField.ID: PersonModel.id,
            PersonSortField.NAME: PersonModel.name,
            PersonSortField.BIRTH_DAY: PersonModel.birth_date,
            PersonSortField.GENDER: PersonModel.gender,
        }

        result = await paginate_and_sort(
            model=PersonModel,
            stmt=stmt,
            session=self.session,
            page=query.pagination.page,
            page_size=query.pagination.page_size,
            offset=query.pagination.offset,
            sort_by=query.sort.sort_by,
            sort_order=query.sort.sort_order,
            sortable_columns=SORTABLE_COLUMNS,
        )

        persons = [self._to_entity(m) for m in result.items]

        return PaginatedResult[Person](
            items=persons,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def get_children(self, parent_id: int) -> list[Person]:
        stmt = select(PersonModel).where(
            (PersonModel.father_id == parent_id) | (PersonModel.mother_id == parent_id)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models]

    async def update(self, person: Person) -> Person:
        stmt = select(PersonModel).where(PersonModel.id == person.id)

        result = await self.session.execute(stmt)
        model = result.scalar_one()

        model.name = person.name
        model.gender = person.gender
        model.birth_date = person.birth_date
        model.father_id = person.father_id
        model.mother_id = person.mother_id

        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def delete(self, person_id: int) -> None:
        stmt = delete(PersonModel).where(PersonModel.id == person_id)

        await self.session.execute(stmt)

    def _to_entity(self, model: PersonModel) -> Person:
        return Person(
            id=model.id,
            name=model.name,
            gender=Gender(model.gender),
            birth_date=model.birth_date,
            father_id=model.father_id,
            mother_id=model.mother_id,
        )

    def _to_model(self, entity: Person) -> PersonModel:
        model = PersonModel(
            id=entity.id,
            name=entity.name,
            gender=entity.gender,
            birth_date=entity.birth_date,
            father_id=entity.father_id,
            mother_id=entity.mother_id,
        )

        return model
