from uuid import UUID

import pytest

from app.domain.entities.person import Gender, ParentLink, Person
from app.domain.exceptions.person_exceptions import PersonNotFoundException
from app.domain.shared.dto.pagination_dto import PaginationParams
from app.domain.shared.dto.person_filter_dto import (
    FilterPersonQuery,
    PersonFilterDTO,
    PersonSortField,
)
from app.domain.shared.dto.sorter_dto import SortOrderField, SortParams
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import UnitOfWork


@pytest.mark.asyncio
async def test_create_and_get_person(uow: UnitOfWork):
    async with uow:
        person = Person(tree_id=uow.tree_id, id=None,
            name="Ali",
            gender=Gender.MALE,
            birth_date=None,)

        created = await uow.persons.create(person)

        fetched = await uow.persons.get(created.safe_id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Ali"
        assert fetched.gender == Gender.MALE


@pytest.mark.asyncio
async def test_get_or_raise_not_found(uow: UnitOfWork):
    async with uow:
        with pytest.raises(PersonNotFoundException):
            await uow.persons.get_or_raise(UUID(int=99999))


@pytest.mark.asyncio
async def test_update_person(uow: UnitOfWork):
    async with uow:
        person = Person(tree_id=uow.tree_id, id=None,
            name="Ali",
            gender=Gender.MALE,
            birth_date=None,)

        created = await uow.persons.create(person)

        created.name = "Reza"

        updated = await uow.persons.update(created)

        assert updated.name == "Reza"


@pytest.mark.asyncio
async def test_delete_person(uow: UnitOfWork):
    async with uow:
        person = Person(tree_id=uow.tree_id, id=None,
            name="Ali",
            gender=Gender.MALE,
            birth_date=None,)

        created = await uow.persons.create(person)
        person_id = created.safe_id

        await uow.persons.delete(person_id)

        result = await uow.persons.get(person_id)
        assert result is None

        from sqlalchemy import select

        from app.infrastructure.database.models.person_model import PersonModel

        row = (
            await uow.session.execute(
                select(PersonModel).where(PersonModel.id == person_id)
            )
        ).scalar_one()
        assert row.deleted_at is not None


@pytest.mark.asyncio
async def test_get_children(uow: UnitOfWork):
    async with uow:
        father = await uow.persons.create(
            Person(tree_id=uow.tree_id, id=None,
                name="Father",
                gender=Gender.MALE,
                birth_date=None,)
        )

        child = await uow.persons.create(
            Person(tree_id=uow.tree_id, id=None,
                name="Child",
                gender=Gender.MALE,
                birth_date=None,
                parents=[ParentLink(parent_id=father.safe_id)],
            )
        )

        children = await uow.persons.get_children(father.safe_id)

        assert len(children) == 1
        assert children[0].id == child.id


@pytest.mark.asyncio
async def test_get_by_name(uow: UnitOfWork):
    async with uow:
        user_1 = await uow.persons.create(
            Person(tree_id=uow.tree_id, id=None,
                name="user_1",
                gender=Gender.MALE,
                birth_date=None,)
        )

        user_2 = await uow.persons.create(
            Person(tree_id=uow.tree_id, id=None,
                name="user_2",
                gender=Gender.FEMALE,
                birth_date=None,)
        )

        user_3 = await uow.persons.create(
            Person(tree_id=uow.tree_id, id=None,
                name="user_3",
                gender=Gender.MALE,
                birth_date=None,
                parents=[
                    ParentLink(parent_id=user_1.safe_id),
                    ParentLink(parent_id=user_2.safe_id),
                ],
            )
        )

        find = await uow.persons.get_by_name(
            name=user_3.name, marriage_id=None, tree_id=uow.tree_id
        )

        assert find is not None
        assert find.safe_id == user_3.id


@pytest.mark.asyncio
async def test_get_list_by_filter_name(uow: UnitOfWork):
    async with uow:
        await uow.persons.create(
            Person(tree_id=uow.tree_id, id=None,
                name="Ali",
                gender=Gender.MALE,
                birth_date=None,)
        )
        await uow.persons.create(
            Person(tree_id=uow.tree_id, id=None,
                name="Alireza",
                gender=Gender.MALE,
                birth_date=None,)
        )
        await uow.persons.create(
            Person(tree_id=uow.tree_id, id=None,
                name="Sara",
                gender=Gender.FEMALE,
                birth_date=None,)
        )

        query = FilterPersonQuery(
            filters=PersonFilterDTO(
                name="Ali",
                gender=None,
                birth_date=None,
            ),
            pagination=PaginationParams(page=1, page_size=10, offset=0),
            sort=SortParams(
                sort_by=PersonSortField.NAME,
                sort_order=SortOrderField.ASC,
            ),
        )

        result = await uow.persons.get_list_by_filter(query)

        names = [p.name for p in result.items]

        assert "Ali" in names
        assert "Alireza" in names
        assert "Sara" not in names


@pytest.mark.asyncio
async def test_get_list_by_filter_gender(uow: UnitOfWork):
    async with uow:
        await uow.persons.create(
            Person(tree_id=uow.tree_id, id=None,
                name="Ali",
                gender=Gender.MALE,
                birth_date=None,)
        )
        await uow.persons.create(
            Person(tree_id=uow.tree_id, id=None,
                name="Sara",
                gender=Gender.FEMALE,
                birth_date=None,)
        )

        query = FilterPersonQuery(
            filters=PersonFilterDTO(
                gender=Gender.FEMALE,
            ),
            pagination=PaginationParams(page=1, page_size=10, offset=0),
            sort=SortParams(
                sort_by=PersonSortField.ID,
                sort_order=SortOrderField.ASC,
            ),
        )

        result = await uow.persons.get_list_by_filter(query)

        assert len(result.items) == 1
        assert result.items[0].name == "Sara"


@pytest.mark.asyncio
async def test_get_list_by_filter_pagination(uow: UnitOfWork):
    async with uow:
        for i in range(15):
            await uow.persons.create(
                Person(tree_id=uow.tree_id, id=None,
                    name=f"person{i}",
                    gender=Gender.MALE,
                    birth_date=None,)
            )

        query = FilterPersonQuery(
            filters=PersonFilterDTO(),
            pagination=PaginationParams(page=1, page_size=10, offset=0),
            sort=SortParams(
                sort_by=PersonSortField.ID,
                sort_order=SortOrderField.ASC,
            ),
        )

        result = await uow.persons.get_list_by_filter(query)

        assert len(result.items) == 10
        assert result.total >= 15
