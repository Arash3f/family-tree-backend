from collections.abc import Mapping
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.person import (
    Gender,
    ParentLink,
    ParentRelationshipType,
    Person,
)
from app.domain.repositories.person_repository import PersonRepository
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.person_filter_dto import FilterPersonQuery, PersonSortField
from app.infrastructure.database.models.parent_link_model import ParentLinkModel
from app.infrastructure.database.models.person_model import PersonModel
from app.infrastructure.database.utils.pagination_and_sort import paginate_and_sort
from app.infrastructure.database.utils.range_filter import apply_range_filter


class SQLPersonRepository(PersonRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _active_person_stmt(self):
        return (
            select(PersonModel)
            .options(selectinload(PersonModel.parent_links))
            .where(PersonModel.deleted_at.is_(None))
        )

    async def create(self, person: Person) -> Person:
        model = self._to_model(person)

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model, attribute_names=["parent_links"])

        return self._to_entity(model)

    async def get(self, person_id: UUID) -> Person | None:
        stmt = self._active_person_stmt().where(PersonModel.id == person_id)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_by_name(
        self, name: str, marriage_id: UUID | None, tree_id: UUID
    ) -> Person | None:
        stmt = self._active_person_stmt().where(
            PersonModel.name == name,
            PersonModel.marriage_id == marriage_id,
            PersonModel.tree_id == tree_id,
        )
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_list_by_filter(
        self, query: FilterPersonQuery
    ) -> PaginatedResult[Person]:
        stmt = self._active_person_stmt()
        filters = query.filters

        if filters:
            if filters.tree_id:
                stmt = stmt.where(PersonModel.tree_id == filters.tree_id)

            if filters.name:
                stmt = stmt.where(
                    PersonModel.name.contains(filters.name, autoescape=True)
                )

            if filters.id:
                stmt = stmt.where(PersonModel.id == filters.id)

            if filters.gender:
                stmt = stmt.where(PersonModel.gender == filters.gender)

            if filters.marriage_id:
                stmt = stmt.where(PersonModel.marriage_id == filters.marriage_id)

            if filters.parent_id:
                parent_stmt = select(ParentLinkModel.child_id).where(
                    ParentLinkModel.parent_id == filters.parent_id
                )
                if filters.relationship_type:
                    parent_stmt = parent_stmt.where(
                        ParentLinkModel.relationship_type
                        == filters.relationship_type.value
                    )
                stmt = stmt.where(PersonModel.id.in_(parent_stmt))

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

    async def get_children(self, parent_id: UUID) -> list[Person]:
        child_ids = select(ParentLinkModel.child_id).where(
            ParentLinkModel.parent_id == parent_id
        )
        stmt = self._active_person_stmt().where(PersonModel.id.in_(child_ids))

        result = await self.session.execute(stmt)
        models = result.scalars().unique().all()

        return [self._to_entity(m) for m in models]

    async def count_in_tree(self, tree_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(PersonModel)
            .where(
                PersonModel.tree_id == tree_id,
                PersonModel.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def get_by_tree_id(self, tree_id: UUID) -> list[Person]:
        stmt = self._active_person_stmt().where(PersonModel.tree_id == tree_id)

        result = await self.session.execute(stmt)
        models = result.scalars().unique().all()

        return [self._to_entity(m) for m in models]

    async def update(self, person: Person) -> Person:
        stmt = (
            select(PersonModel)
            .options(selectinload(PersonModel.parent_links))
            .where(PersonModel.id == person.id, PersonModel.deleted_at.is_(None))
        )

        result = await self.session.execute(stmt)
        model = result.scalar_one()

        model.name = person.name
        model.family_name = person.family_name
        model.gender = person.gender
        model.birth_date = person.birth_date
        model.death_date = person.death_date
        model.birth_place = person.birth_place
        model.death_place = person.death_place
        model.notes = person.notes
        model.tree_id = person.tree_id
        model.marriage_id = person.marriage_id
        model.photo_object_key = person.photo_object_key
        model.deleted_at = person.deleted_at

        existing_by_parent = {link.parent_id: link for link in model.parent_links}

        for parent_id, existing in list(existing_by_parent.items()):
            matching = next(
                (link for link in person.parents if link.parent_id == parent_id),
                None,
            )
            if matching is None:
                model.parent_links.remove(existing)
            elif existing.relationship_type != matching.relationship_type.value:
                existing.relationship_type = matching.relationship_type.value

        existing_parent_ids = {link.parent_id for link in model.parent_links}
        for link in person.parents:
            if link.parent_id not in existing_parent_ids:
                model.parent_links.append(
                    ParentLinkModel(
                        child_id=person.safe_id,
                        parent_id=link.parent_id,
                        relationship_type=link.relationship_type.value,
                    )
                )

        await self.session.flush()
        await self.session.refresh(model, attribute_names=["parent_links"])

        return self._to_entity(model)

    async def delete(self, person_id: UUID) -> None:
        stmt = (
            update(PersonModel)
            .where(PersonModel.id == person_id, PersonModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)

    def _to_entity(self, model: PersonModel) -> Person:
        return Person(
            id=model.id,
            name=model.name,
            gender=Gender(model.gender),
            tree_id=model.tree_id,
            birth_date=model.birth_date,
            death_date=model.death_date,
            parents=[
                ParentLink(
                    parent_id=link.parent_id,
                    relationship_type=ParentRelationshipType(link.relationship_type),
                )
                for link in model.parent_links
            ],
            marriage_id=model.marriage_id,
            family_name=model.family_name,
            birth_place=model.birth_place,
            death_place=model.death_place,
            notes=model.notes,
            photo_object_key=model.photo_object_key,
            deleted_at=model.deleted_at,
        )

    def _to_model(self, entity: Person) -> PersonModel:
        model = PersonModel(
            id=entity.id,
            name=entity.name,
            family_name=entity.family_name,
            gender=entity.gender,
            birth_date=entity.birth_date,
            death_date=entity.death_date,
            birth_place=entity.birth_place,
            death_place=entity.death_place,
            notes=entity.notes,
            tree_id=entity.tree_id,
            marriage_id=entity.marriage_id,
            photo_object_key=entity.photo_object_key,
            deleted_at=entity.deleted_at,
        )
        model.parent_links = [
            ParentLinkModel(
                parent_id=link.parent_id,
                relationship_type=link.relationship_type.value,
            )
            for link in entity.parents
        ]
        return model
