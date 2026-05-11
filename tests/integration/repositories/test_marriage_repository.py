from datetime import date

import pytest

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Gender, Person
from app.domain.exceptions.marriage_exceptions import MarriageNotFoundException
from app.domain.shared.dto.marriage_filter_dto import (
    FilterMarriageDTO,
    MarriageFilterDataDTO,
    MarriageSortField,
)
from app.domain.shared.dto.pagination_dto import PaginatedResult, PaginationParams
from app.domain.shared.dto.range_dto import RangeDTO
from app.domain.shared.dto.sorter_dto import SortOrderField, SortParams


@pytest.mark.asyncio
async def test_create_and_get_marriage(uow: UnitOfWork):
    async with uow:
        new_husband = Person(
            id=None,
            father_id=None,
            gender=Gender.MALE,
            name="husband",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        new_wife = Person(
            id=None,
            father_id=None,
            gender=Gender.FEMALE,
            name="wife",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        husband = await uow.persons.create(new_husband)
        wife = await uow.persons.create(new_wife)
        new_marriage = Marriage(
            husband_id=husband.safe_id,
            wife_id=wife.safe_id,
            married_at=date(2020, 1, 1),
            divorced_at=None,
            id=None,
        )
        marriage = await uow.marriages.create(new_marriage)

        fetched = await uow.marriages.get_or_raise(marriage.safe_id)

        assert fetched.id == marriage.id
        assert fetched.divorced_at == new_marriage.divorced_at
        assert fetched.husband_id == new_marriage.husband_id
        assert fetched.wife_id == new_marriage.wife_id
        assert fetched.married_at == new_marriage.married_at


@pytest.mark.asyncio
async def test_get_or_raise_success(uow: UnitOfWork):
    async with uow:
        new_husband = Person(
            id=None,
            father_id=None,
            gender=Gender.MALE,
            name="husband",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        new_wife = Person(
            id=None,
            father_id=None,
            gender=Gender.FEMALE,
            name="wife",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        husband = await uow.persons.create(new_husband)
        wife = await uow.persons.create(new_wife)
        new_marriage = Marriage(
            husband_id=husband.safe_id,
            wife_id=wife.safe_id,
            married_at=date(2020, 1, 1),
            divorced_at=None,
            id=None,
        )
        marriage = await uow.marriages.create(new_marriage)

        fetched = await uow.marriages.get_or_raise(marriage_id=marriage.safe_id)

        assert fetched.id == marriage.id
        assert fetched.divorced_at == new_marriage.divorced_at
        assert fetched.husband_id == new_marriage.husband_id
        assert fetched.wife_id == new_marriage.wife_id
        assert fetched.married_at == new_marriage.married_at


@pytest.mark.asyncio
async def test_get_or_raise_not_found(uow: UnitOfWork):
    async with uow:
        with pytest.raises(MarriageNotFoundException):
            await uow.marriages.get_or_raise(marriage_id=999)


@pytest.mark.asyncio
async def test_update_marriage(uow: UnitOfWork):
    async with uow:
        new_husband = Person(
            id=None,
            father_id=None,
            gender=Gender.MALE,
            name="husband",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        new_wife = Person(
            id=None,
            father_id=None,
            gender=Gender.FEMALE,
            name="wife",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        husband = await uow.persons.create(new_husband)
        wife = await uow.persons.create(new_wife)
        new_marriage = Marriage(
            husband_id=husband.safe_id,
            wife_id=wife.safe_id,
            married_at=date(2020, 1, 1),
            divorced_at=None,
            id=None,
        )
        marriage = await uow.marriages.create(new_marriage)

        new_husband_2 = Person(
            id=None,
            father_id=None,
            gender=Gender.MALE,
            name="husband",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        new_wife_2 = Person(
            id=None,
            father_id=None,
            gender=Gender.FEMALE,
            name="wife",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        husband_2 = await uow.persons.create(new_husband_2)
        wife_2 = await uow.persons.create(new_wife_2)

        marriage.divorced_at = date(2002, 1, 1)
        marriage.husband_id = husband_2.safe_id
        marriage.wife_id = wife_2.safe_id
        marriage.married_at = date(2001, 1, 1)

        updated = await uow.marriages.update(marriage=marriage)

        assert updated.wife_id == wife_2.safe_id
        assert updated.husband_id == husband_2.safe_id
        assert updated.divorced_at == date(2002, 1, 1)
        assert updated.married_at == date(2001, 1, 1)


@pytest.mark.asyncio
async def test_update_marriage_not_found(uow: UnitOfWork):
    async with uow:
        marriage = Marriage(
            husband_id=1,
            wife_id=2,
            married_at=date(2020, 1, 1),
            divorced_at=None,
            id=111,
        )
        with pytest.raises(MarriageNotFoundException):
            await uow.marriages.update(marriage=marriage)


@pytest.mark.asyncio
async def test_get_list_by_filter_with_husband_and_wife_id(uow: UnitOfWork):
    async with uow:
        # persons for first marriage
        husband_1 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.MALE,
                name="husband_1",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )
        wife_1 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.FEMALE,
                name="wife_1",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )

        # persons for second marriage
        husband_2 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.MALE,
                name="husband_2",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )
        wife_2 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.FEMALE,
                name="wife_2",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )

        cr_1 = await uow.marriages.create(
            Marriage(
                id=None,
                husband_id=husband_1.safe_id,
                wife_id=wife_1.safe_id,
                married_at=date(2020, 1, 1),
                divorced_at=None,
            )
        )

        await uow.marriages.create(
            Marriage(
                id=None,
                husband_id=husband_2.safe_id,
                wife_id=wife_2.safe_id,
                married_at=date(2021, 1, 1),
                divorced_at=None,
            )
        )

        # Creata 2 object

        query = FilterMarriageDTO(
            filters=MarriageFilterDataDTO(
                husband_id=husband_1.safe_id,
                wife_id=wife_1.safe_id,
            ),
            pagination=PaginationParams(
                page=1,
                page_size=5,
                offset=0,
            ),
            sort=SortParams(
                sort_by=MarriageSortField.ID,
                sort_order=SortOrderField.ASC,
            ),
        )

        result: PaginatedResult[Marriage] = await uow.marriages.get_list_by_filter(
            query
        )

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == cr_1.safe_id


@pytest.mark.asyncio
async def test_get_list_by_filter_with_married_and_divorced_at(uow: UnitOfWork):
    async with uow:
        # persons for first marriage
        husband_1 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.MALE,
                name="husband_1",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )
        wife_1 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.FEMALE,
                name="wife_1",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )

        # persons for second marriage
        husband_2 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.MALE,
                name="husband_2",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )
        wife_2 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.FEMALE,
                name="wife_2",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )

        await uow.marriages.create(
            Marriage(
                id=None,
                husband_id=husband_1.safe_id,
                wife_id=wife_1.safe_id,
                married_at=date(2020, 1, 1),
                divorced_at=date(2025, 1, 1),
            )
        )

        cr_2 = await uow.marriages.create(
            Marriage(
                id=None,
                husband_id=husband_2.safe_id,
                wife_id=wife_2.safe_id,
                married_at=date(2021, 1, 1),
                divorced_at=date(2022, 1, 1),
            )
        )

        # Creata 2 object

        query = FilterMarriageDTO(
            filters=MarriageFilterDataDTO(
                married_at=RangeDTO(
                    min=date(1999, 1, 1),
                    max=date(2022, 1, 1),
                ),
                divorced_at=RangeDTO(
                    min=date(2022, 1, 1),
                    max=date(2024, 1, 1),
                ),
            ),
            pagination=PaginationParams(
                page=1,
                page_size=5,
                offset=0,
            ),
            sort=SortParams(
                sort_by=MarriageSortField.ID,
                sort_order=SortOrderField.ASC,
            ),
        )

        result: PaginatedResult[Marriage] = await uow.marriages.get_list_by_filter(
            query
        )

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == cr_2.safe_id


@pytest.mark.asyncio
async def test_get_list_without_filter(uow: UnitOfWork):
    async with uow:
        # persons for first marriage
        husband_1 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.MALE,
                name="husband_1",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )
        wife_1 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.FEMALE,
                name="wife_1",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )

        # persons for second marriage
        husband_2 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.MALE,
                name="husband_2",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )
        wife_2 = await uow.persons.create(
            Person(
                id=None,
                father_id=None,
                gender=Gender.FEMALE,
                name="wife_2",
                mother_id=None,
                birth_date=date(2000, 1, 1),
            )
        )

        await uow.marriages.create(
            Marriage(
                id=None,
                husband_id=husband_1.safe_id,
                wife_id=wife_1.safe_id,
                married_at=date(2020, 1, 1),
                divorced_at=None,
            )
        )

        await uow.marriages.create(
            Marriage(
                id=None,
                husband_id=husband_2.safe_id,
                wife_id=wife_2.safe_id,
                married_at=date(2021, 1, 1),
                divorced_at=None,
            )
        )

        await uow.marriages.create(
            Marriage(
                id=None,
                husband_id=husband_1.safe_id,
                wife_id=wife_2.safe_id,
                married_at=date(2021, 1, 1),
                divorced_at=None,
            )
        )

        cr_4 = await uow.marriages.create(
            Marriage(
                id=None,
                husband_id=husband_2.safe_id,
                wife_id=wife_1.safe_id,
                married_at=date(2021, 1, 1),
                divorced_at=None,
            )
        )

        # Creata 4 object

        query = FilterMarriageDTO(
            pagination=PaginationParams(
                page=2,
                page_size=1,
                offset=2,
            ),
            sort=SortParams(
                sort_by=MarriageSortField.ID,
                sort_order=SortOrderField.ASC,
            ),
        )

        result: PaginatedResult[Marriage] = await uow.marriages.get_list_by_filter(
            query
        )

        assert result.total == 4
        assert len(result.items) == 1
        assert result.items[0].id == cr_4.safe_id


@pytest.mark.asyncio
async def test_get_list_by_filter_with_pagination(uow: UnitOfWork):
    async with uow:
        created_marriages = []

        for i in range(10):
            husband = await uow.persons.create(
                Person(
                    id=None,
                    father_id=None,
                    gender=Gender.MALE,
                    name=f"husband_{i}",
                    mother_id=None,
                    birth_date=date(2000, 1, 1),
                )
            )
            wife = await uow.persons.create(
                Person(
                    id=None,
                    father_id=None,
                    gender=Gender.FEMALE,
                    name=f"wife_{i}",
                    mother_id=None,
                    birth_date=date(2000, 1, 1),
                )
            )

            marriage = await uow.marriages.create(
                Marriage(
                    id=None,
                    husband_id=husband.safe_id,
                    wife_id=wife.safe_id,
                    married_at=date(2020, 1, i + 1),
                    divorced_at=None,
                )
            )
            created_marriages.append(marriage)

        query = FilterMarriageDTO(
            pagination=PaginationParams(
                page=2,
                page_size=2,
                offset=5,
            ),
            sort=SortParams(
                sort_by=MarriageSortField.ID,
                sort_order=SortOrderField.ASC,
            ),
        )

        result: PaginatedResult[Marriage] = await uow.marriages.get_list_by_filter(
            query
        )

        assert result.page == query.pagination.page
        assert result.page_size == query.pagination.page_size
        assert len(result.items) == query.pagination.page_size
        assert result.total == 10

        returned_ids = [item.id for item in result.items]

        expected_ids = [
            created_marriages[7].id,
            created_marriages[8].id,
        ]

        assert returned_ids == expected_ids


@pytest.mark.asyncio
async def test_get_by_ids(uow: UnitOfWork):
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

        marriage = await uow.marriages.create(
            Marriage(
                id=None,
                married_at=date(2000, 1, 1),
                wife_id=user_2.safe_id,
                husband_id=user_1.safe_id,
            )
        )

        find = await uow.marriages.get_by_ids(
            wife_id=user_2.safe_id,
            husband_id=user_1.safe_id,
        )

        assert find is not None
        assert find.safe_id == marriage.id


@pytest.mark.asyncio
async def test_end_marriage(uow: UnitOfWork):
    async with uow:
        new_husband = Person(
            id=None,
            father_id=None,
            gender=Gender.MALE,
            name="husband",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        new_wife = Person(
            id=None,
            father_id=None,
            gender=Gender.FEMALE,
            name="wife",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        husband = await uow.persons.create(new_husband)
        wife = await uow.persons.create(new_wife)
        new_marriage = Marriage(
            husband_id=husband.safe_id,
            wife_id=wife.safe_id,
            married_at=date(2020, 1, 1),
            divorced_at=None,
            id=None,
        )
        marriage = await uow.marriages.create(new_marriage)

        divorce_date = date(2023, 1, 1)

        await uow.marriages.end(marriage.safe_id, divorced_at=divorce_date)
        updated = await uow.marriages.get_or_raise(marriage_id=marriage.safe_id)

        assert updated.divorced_at == divorce_date


@pytest.mark.asyncio
async def test_delete_marriage(uow: UnitOfWork):
    async with uow:
        new_husband = Person(
            id=None,
            father_id=None,
            gender=Gender.MALE,
            name="husband",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        new_wife = Person(
            id=None,
            father_id=None,
            gender=Gender.FEMALE,
            name="wife",
            mother_id=None,
            birth_date=date(2000, 1, 1),
        )
        husband = await uow.persons.create(new_husband)
        wife = await uow.persons.create(new_wife)
        new_marriage = Marriage(
            husband_id=husband.safe_id,
            wife_id=wife.safe_id,
            married_at=date(2020, 1, 1),
            divorced_at=None,
            id=None,
        )
        marriage = await uow.marriages.create(marriage=new_marriage)

        await uow.marriages.delete(marriage_id=marriage.safe_id)
        fetched = await uow.marriages.get(marriage_id=marriage.safe_id)

        assert fetched is None
