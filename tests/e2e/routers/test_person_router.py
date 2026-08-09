from datetime import date
from uuid import UUID

import pytest
from pydantic import TypeAdapter

from app.domain.entities.person import Gender, Person
from app.domain.shared.dto.person_filter_dto import PersonSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork
from app.presentation.rest.schemas.dto.common import (
    PaginatedResponse,
    PaginationRequestParams,
    ResultResponse,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.person_schema import (
    FilterPersonRequest,
    ParentLinkRequest,
    PersonCreateRequest,
    PersonCreateResponse,
    PersonFilterRequestData,
    PersonModel,
    PersonUpdateRequest,
    PersonUpdateResponse,
    _PersonUpdateDateRequest,
    _PersonUpdateWhereRequest,
)
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.e2e.auth_headers import member_headers as member_headers

BASE_URL = "/persons"


# ============================================================
# CREATE PERSON
# ============================================================


@pytest.mark.asyncio
async def test_create_person_permission_denied(client, member_headers):  # noqa: F811
    req = PersonCreateRequest(
        name="limited-person",
        gender=Gender.MALE,
    )
    resp = await client.post(
        f"{BASE_URL}/",
        json=req.model_dump(mode="json"),
        headers=member_headers,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_create_person_unauthenticated(client):
    req = PersonCreateRequest(
        name="limited-person",
        gender=Gender.MALE,
    )
    resp = await client.post(
        f"{BASE_URL}/",
        json=req.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_person_success(client, admin_headers, uow):  # noqa: F811
    father = await uow.persons.create(
        Person(
            id=None,
            name="father",
            gender=Gender.MALE,
            birth_date=date(1970, 1, 1),
        )
    )
    mother = await uow.persons.create(
        Person(
            id=None,
            name="mother",
            gender=Gender.FEMALE,
            birth_date=date(1972, 1, 1),
        )
    )
    await uow.commit()

    req = PersonCreateRequest(
        name="child",
        gender=Gender.MALE,
        parents=[
            ParentLinkRequest(parent_id=father.safe_id),
            ParentLinkRequest(parent_id=mother.safe_id),
        ],
    )

    resp = await client.post(
        f"{BASE_URL}/",
        json=req.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 200

    person_data = TypeAdapter(PersonCreateResponse).validate_python(resp.json())
    assert person_data.id is not None
    assert person_data.name == req.name
    assert person_data.gender == req.gender
    assert {p.parent_id for p in person_data.parents} == {
        father.safe_id,
        mother.safe_id,
    }

    async with uow:
        find_person = await uow.persons.get_or_raise(person_id=person_data.id)

    assert find_person.id == person_data.id
    assert find_person.name == person_data.name
    assert set(find_person.parent_ids) == {father.safe_id, mother.safe_id}


# ============================================================
# GET PERSON
# ============================================================


@pytest.mark.asyncio
async def test_get_person_permission_denied(client, member_headers):  # noqa: F811
    resp = await client.get(
        f"{BASE_URL}/{UUID(int=1)}",
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_person_unauthenticated(client):
    resp = await client.get(f"{BASE_URL}/{UUID(int=1)}")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_person_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    person = await uow.persons.create(
        Person(
            id=None,
            name="Ali",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
        )
    )
    await uow.commit()

    resp = await client.get(
        f"{BASE_URL}/{person.safe_id}",
        headers=admin_headers,
    )

    assert resp.status_code == 200

    data = resp.json()
    assert data["id"] == str(person.safe_id)
    assert data["name"] == person.name
    assert data["gender"] == person.gender.value
    assert data["birth_date"] is not None
    assert data["parents"] == []
    assert data.get("marriage_id") is None


@pytest.mark.asyncio
async def test_get_person_with_invalid_id(client, admin_headers):  # noqa: F811
    resp = await client.get(
        f"{BASE_URL}/{UUID(int=999999)}",
        headers=admin_headers,
    )

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == 1104
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERSON_NOT_FOUND]


# ============================================================
# UPDATE PERSON
# ============================================================


@pytest.mark.asyncio
async def test_update_person_permission_denied(client, member_headers):  # noqa: F811
    payload = PersonUpdateRequest(
        where=_PersonUpdateWhereRequest(person_id=UUID(int=1)),
        data=_PersonUpdateDateRequest(name="updated"),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(mode="json"),
        headers=member_headers,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_update_person_unauthenticated(client):
    payload = PersonUpdateRequest(
        where=_PersonUpdateWhereRequest(person_id=UUID(int=1)),
        data=_PersonUpdateDateRequest(name="updated"),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_person_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    person = await uow.persons.create(
        Person(
            id=None,
            name="old-name",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
        )
    )
    await uow.commit()

    payload = PersonUpdateRequest(
        where=_PersonUpdateWhereRequest(person_id=person.safe_id),
        data=_PersonUpdateDateRequest(name="new-name", gender=Gender.FEMALE),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 200
    TypeAdapter(PersonUpdateResponse).validate_python(resp.json())

    async with uow:
        updated = await uow.persons.get_or_raise(person_id=person.safe_id)

    assert updated.name == payload.data.name
    assert updated.gender == payload.data.gender


@pytest.mark.asyncio
async def test_update_person_with_invalid_id(client, admin_headers):  # noqa: F811
    payload = PersonUpdateRequest(
        where=_PersonUpdateWhereRequest(person_id=UUID(int=88888)),
        data=_PersonUpdateDateRequest(name="new-name"),
    )

    resp = await client.put(
        f"{BASE_URL}/",
        json=payload.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == 1104
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERSON_NOT_FOUND]


# ============================================================
# DELETE PERSON
# ============================================================


@pytest.mark.asyncio
async def test_delete_person_permission_denied(client, member_headers):  # noqa: F811
    resp = await client.delete(
        f"{BASE_URL}/{UUID(int=1)}",
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_delete_person_unauthenticated(client):
    resp = await client.delete(f"{BASE_URL}/{UUID(int=1)}")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_person_success(client, admin_headers, uow: SQLAlchemyUnitOfWork):  # noqa: F811
    person = await uow.persons.create(
        Person(
            id=None,
            name="to-delete",
            gender=Gender.MALE,
        )
    )
    await uow.commit()

    resp = await client.delete(
        f"{BASE_URL}/{person.safe_id}",
        headers=admin_headers,
    )

    assert resp.status_code == 200
    TypeAdapter(ResultResponse).validate_python(resp.json())

    deleted_person_id = person.safe_id
    async with uow:
        deleted = await uow.persons.get(person_id=deleted_person_id)

    assert deleted is None


@pytest.mark.asyncio
async def test_delete_person_with_invalid_id(client, admin_headers):  # noqa: F811
    resp = await client.delete(
        f"{BASE_URL}/{UUID(int=999999)}",
        headers=admin_headers,
    )

    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == 1104
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERSON_NOT_FOUND]


# ============================================================
# LIST PERSONS
# ============================================================


@pytest.mark.asyncio
async def test_get_person_list_by_filter_permission_denied(client, member_headers):  # noqa: F811
    req = FilterPersonRequest(
        filters=PersonFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(mode="json"),
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == 1301
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]


@pytest.mark.asyncio
async def test_get_person_list_by_filter_unauthenticated(client):
    req = FilterPersonRequest(
        filters=PersonFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_person_list_by_filter_success(
    client,
    admin_headers,  # noqa: F811
    uow: SQLAlchemyUnitOfWork,
):
    person1 = await uow.persons.create(
        Person(id=None, name="cus_person1", gender=Gender.MALE)
    )
    person2 = await uow.persons.create(
        Person(id=None, name="cus_person2", gender=Gender.FEMALE)
    )
    person3 = await uow.persons.create(
        Person(id=None, name="cus_person3", gender=Gender.MALE)
    )
    person4 = await uow.persons.create(
        Person(id=None, name="cus_person4", gender=Gender.FEMALE)
    )
    person5 = await uow.persons.create(
        Person(id=None, name="cus_person5", gender=Gender.MALE)
    )
    await uow.commit()

    req = FilterPersonRequest(
        filters=PersonFilterRequestData(name="cus_person"),
        pagination=PaginationRequestParams(offset=1, page=2, page_size=2),
        sort=SortRequestParams(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.ASC,
        ),
    )

    resp = await client.post(
        f"{BASE_URL}/list",
        json=req.model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 200

    data = TypeAdapter(PaginatedResponse[PersonModel]).validate_python(resp.json())
    sorted_persons = sorted(
        [person1, person2, person3, person4, person5],
        key=lambda person: person.safe_id,
    )
    start = req.pagination.offset + (req.pagination.page - 1) * req.pagination.page_size
    expected = sorted_persons[start : start + req.pagination.page_size]

    assert len(data.items) == 2
    assert data.items[0].id == expected[0].safe_id
    assert data.items[0].name == expected[0].name
    assert data.items[1].id == expected[1].safe_id
    assert data.items[1].name == expected[1].name
