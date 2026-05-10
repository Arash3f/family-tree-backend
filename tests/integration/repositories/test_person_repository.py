import pytest

from app.domain.entities.person import Gender, Person
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
        person = Person(
            id=None,
            name="Ali",
            gender=Gender.MALE,
            birth_date=None,
            father_id=None,
            mother_id=None,
        )

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
            await uow.persons.get_or_raise(99999)


@pytest.mark.asyncio
async def test_update_person(uow: UnitOfWork):
    async with uow:
        person = Person(
            id=None,
            name="Ali",
            gender=Gender.MALE,
            birth_date=None,
            father_id=None,
            mother_id=None,
        )

        created = await uow.persons.create(person)

        created.name = "Reza"

        updated = await uow.persons.update(created)

        assert updated.name == "Reza"


@pytest.mark.asyncio
async def test_delete_person(uow: UnitOfWork):
    async with uow:
        person = Person(
            id=None,
            name="Ali",
            gender=Gender.MALE,
            birth_date=None,
            father_id=None,
            mother_id=None,
        )

        created = await uow.persons.create(person)

        await uow.persons.delete(created.safe_id)

        result = await uow.persons.get(created.safe_id)

        assert result is None


@pytest.mark.asyncio
async def test_get_children(uow: UnitOfWork):
    async with uow:
        father = await uow.persons.create(
            Person(
                id=None,
                name="Father",
                gender=Gender.MALE,
                birth_date=None,
                father_id=None,
                mother_id=None,
            )
        )

        child = await uow.persons.create(
            Person(
                id=None,
                name="Child",
                gender=Gender.MALE,
                birth_date=None,
                father_id=father.id,
                mother_id=None,
            )
        )

        children = await uow.persons.get_children(father.safe_id)

        assert len(children) == 1
        assert children[0].id == child.id


@pytest.mark.asyncio
async def test_get_by_name(uow: UnitOfWork):
    async with uow:
        user_1 = await uow.persons.create(
            Person(
                id=None,
                name="user_1",
                gender=Gender.MALE,
                birth_date=None,
                father_id=None,
                mother_id=None,
            )
        )

        user_2 = await uow.persons.create(
            Person(
                id=None,
                name="user_2",
                gender=Gender.FEMALE,
                birth_date=None,
                father_id=None,
                mother_id=None,
            )
        )

        user_3 = await uow.persons.create(
            Person(
                id=None,
                name="user_3",
                gender=Gender.MALE,
                birth_date=None,
                father_id=user_1.id,
                mother_id=user_2.id,
            )
        )

        find = await uow.persons.get_by_name(
            name=user_3.name, father_id=user_1.id, mother_id=user_2.id
        )

        assert find is not None
        assert find.safe_id == user_3.id


@pytest.mark.asyncio
async def test_get_list_by_filter_name(uow: UnitOfWork):
    async with uow:
        await uow.persons.create(
            Person(
                id=None,
                name="Ali",
                gender=Gender.MALE,
                birth_date=None,
                father_id=None,
                mother_id=None,
            )
        )
        await uow.persons.create(
            Person(
                id=None,
                name="Alireza",
                gender=Gender.MALE,
                birth_date=None,
                father_id=None,
                mother_id=None,
            )
        )
        await uow.persons.create(
            Person(
                id=None,
                name="Sara",
                gender=Gender.FEMALE,
                birth_date=None,
                father_id=None,
                mother_id=None,
            )
        )

        query = FilterPersonQuery(
            filters=PersonFilterDTO(
                name="Ali",
                gender=None,
                father_id=None,
                mother_id=None,
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
            Person(
                id=None,
                name="Ali",
                gender=Gender.MALE,
                birth_date=None,
                father_id=None,
                mother_id=None,
            )
        )
        await uow.persons.create(
            Person(
                id=None,
                name="Sara",
                gender=Gender.FEMALE,
                birth_date=None,
                father_id=None,
                mother_id=None,
            )
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
                Person(None, f"person{i}", Gender.MALE, None, None, None)
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
