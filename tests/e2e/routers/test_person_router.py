from datetime import date
from uuid import UUID

import pytest
from pydantic import TypeAdapter

from app.domain.entities.person import Gender, Person
from app.domain.shared.dto.person_filter_dto import PersonSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
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
from tests.helpers.uow import TreeUnitOfWork


def persons_url(tree_id: UUID, suffix: str = "") -> str:
    return f"/family-trees/{tree_id}/persons{suffix}"


# ============================================================
# CREATE PERSON
# ============================================================


@pytest.mark.asyncio
async def test_create_person_permission_denied(client, tree_id, member_headers):  # noqa: F811
    req = PersonCreateRequest(
        name="limited-person",
        gender=Gender.MALE,
    )
    resp = await client.post(
        persons_url(tree_id),
        json=req.model_dump(mode="json"),
        headers=member_headers,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_create_person_unauthenticated(client, tree_id):
    req = PersonCreateRequest(
        name="limited-person",
        gender=Gender.MALE,
    )
    resp = await client.post(
        persons_url(tree_id),
        json=req.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_person_success(client, tree_id, admin_headers, uow):  # noqa: F811
    father = await uow.persons.create(
        Person(
            tree_id=uow.tree_id,
            id=None,
            name="father",
            gender=Gender.MALE,
            birth_date=date(1970, 1, 1),
        )
    )
    mother = await uow.persons.create(
        Person(
            tree_id=uow.tree_id,
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
        persons_url(tree_id),
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
async def test_get_person_permission_denied(client, tree_id, member_headers):  # noqa: F811
    resp = await client.get(
        persons_url(tree_id, f"/{UUID(int=1)}"),
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_get_person_unauthenticated(client, tree_id):
    resp = await client.get(persons_url(tree_id, f"/{UUID(int=1)}"))

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_person_success(client, tree_id, admin_headers, uow: TreeUnitOfWork):  # noqa: F811
    person = await uow.persons.create(
        Person(
            tree_id=uow.tree_id,
            id=None,
            name="Ali",
            gender=Gender.MALE,
            birth_date=date(1990, 1, 1),
        )
    )
    await uow.commit()

    resp = await client.get(
        persons_url(tree_id, f"/{person.safe_id}"),
        headers=admin_headers,
    )

    assert resp.status_code == 200

    data = resp.json()
    assert data["id"] == str(person.safe_id)
    assert data["name"] == person.name
    assert data["gender"] == person.gender.value
    assert data["birth_date"] == "1990-01-01"
    assert data["parents"] == []
    assert data.get("marriage_id") is None


@pytest.mark.asyncio
async def test_get_person_with_invalid_id(client, tree_id, admin_headers):  # noqa: F811
    resp = await client.get(
        persons_url(tree_id, f"/{UUID(int=999999)}"),
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
async def test_update_person_permission_denied(client, tree_id, member_headers):  # noqa: F811
    payload = PersonUpdateRequest(
        where=_PersonUpdateWhereRequest(person_id=UUID(int=1)),
        data=_PersonUpdateDateRequest(name="updated"),
    )

    resp = await client.put(
        persons_url(tree_id),
        json=payload.model_dump(mode="json"),
        headers=member_headers,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_update_person_unauthenticated(client, tree_id):
    payload = PersonUpdateRequest(
        where=_PersonUpdateWhereRequest(person_id=UUID(int=1)),
        data=_PersonUpdateDateRequest(name="updated"),
    )

    resp = await client.put(
        persons_url(tree_id),
        json=payload.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_person_success(
    client, tree_id, admin_headers, uow: TreeUnitOfWork
):  # noqa: F811
    person = await uow.persons.create(
        Person(
            tree_id=uow.tree_id,
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
        persons_url(tree_id),
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
async def test_update_person_with_invalid_id(client, tree_id, admin_headers):  # noqa: F811
    payload = PersonUpdateRequest(
        where=_PersonUpdateWhereRequest(person_id=UUID(int=88888)),
        data=_PersonUpdateDateRequest(name="new-name"),
    )

    resp = await client.put(
        persons_url(tree_id),
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
async def test_delete_person_permission_denied(client, tree_id, member_headers):  # noqa: F811
    resp = await client.delete(
        persons_url(tree_id, f"/{UUID(int=1)}"),
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_delete_person_unauthenticated(client, tree_id):
    resp = await client.delete(persons_url(tree_id, f"/{UUID(int=1)}"))

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_person_success(
    client, tree_id, admin_headers, uow: TreeUnitOfWork
):  # noqa: F811
    person = await uow.persons.create(
        Person(
            tree_id=uow.tree_id,
            id=None,
            name="to-delete",
            gender=Gender.MALE,
        )
    )
    await uow.commit()

    resp = await client.delete(
        persons_url(tree_id, f"/{person.safe_id}"),
        headers=admin_headers,
    )

    assert resp.status_code == 200
    TypeAdapter(ResultResponse).validate_python(resp.json())

    deleted_person_id = person.safe_id
    async with uow:
        deleted = await uow.persons.get(person_id=deleted_person_id)

    assert deleted is None


@pytest.mark.asyncio
async def test_delete_person_with_invalid_id(client, tree_id, admin_headers):  # noqa: F811
    resp = await client.delete(
        persons_url(tree_id, f"/{UUID(int=999999)}"),
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
async def test_get_person_list_by_filter_permission_denied(
    client, tree_id, member_headers
):  # noqa: F811
    req = FilterPersonRequest(
        filters=PersonFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        persons_url(tree_id, "/list"),
        json=req.model_dump(mode="json"),
        headers=member_headers,
    )

    body = resp.json()
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_get_person_list_by_filter_unauthenticated(client, tree_id):
    req = FilterPersonRequest(
        filters=PersonFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        persons_url(tree_id, "/list"),
        json=req.model_dump(mode="json"),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_person_list_by_filter_success(
    client,
    tree_id,
    admin_headers,  # noqa: F811
    uow: TreeUnitOfWork,
):
    person1 = await uow.persons.create(
        Person(tree_id=uow.tree_id, id=None, name="cus_person1", gender=Gender.MALE)
    )
    person2 = await uow.persons.create(
        Person(tree_id=uow.tree_id, id=None, name="cus_person2", gender=Gender.FEMALE)
    )
    person3 = await uow.persons.create(
        Person(tree_id=uow.tree_id, id=None, name="cus_person3", gender=Gender.MALE)
    )
    person4 = await uow.persons.create(
        Person(tree_id=uow.tree_id, id=None, name="cus_person4", gender=Gender.FEMALE)
    )
    person5 = await uow.persons.create(
        Person(tree_id=uow.tree_id, id=None, name="cus_person5", gender=Gender.MALE)
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
        persons_url(tree_id, "/list"),
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


# ============================================================
# TREE MEMBERSHIP
# ============================================================


async def _reader_headers(client, uow):
    from app.domain.entities.user import User
    from app.infrastructure.services.security.password_hasher_impl import (
        Argon2PasswordHasher,
    )

    hasher = Argon2PasswordHasher()
    reader = await uow.users.create(
        User(
            username="person_reader",
            password_hash=hasher.hash("person_reader"),
        )
    )
    await uow.commit()

    login = await client.post(
        "/auth/login",
        data={"username": "person_reader", "password": "person_reader"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, reader


@pytest.mark.asyncio
async def test_list_persons_denied_for_non_member(client, tree_id, uow):
    headers, _reader = await _reader_headers(client, uow)

    req = FilterPersonRequest(
        filters=PersonFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        persons_url(tree_id, "/list"),
        json=req.model_dump(mode="json"),
        headers=headers,
    )

    assert resp.status_code == 403
    body = resp.json()
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_list_persons_allowed_for_member(client, tree_id, uow):
    headers, reader = await _reader_headers(client, uow)
    from tests.helpers.family_tree import add_tree_member

    await add_tree_member(uow, tree_id=tree_id, user_id=reader.safe_id)
    await uow.commit()

    await uow.persons.create(
        Person(id=None, tree_id=uow.tree_id, name="member-visible", gender=Gender.MALE)
    )
    await uow.commit()

    req = FilterPersonRequest(
        filters=PersonFilterRequestData(name="member-visible"),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await client.post(
        persons_url(tree_id, "/list"),
        json=req.model_dump(mode="json"),
        headers=headers,
    )

    assert resp.status_code == 200
    data = TypeAdapter(PaginatedResponse[PersonModel]).validate_python(resp.json())
    assert data.total >= 1
    assert any(item.name == "member-visible" for item in data.items)


@pytest.mark.asyncio
async def test_person_lists_are_isolated_per_tree(client, admin_headers, uow):
    from tests.helpers.family_tree import create_family_tree_with_owner, get_admin_user

    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Other Tree"
    )
    await uow.commit()

    await uow.persons.create(
        Person(id=None, tree_id=uow.tree_id, name="tree-a-only", gender=Gender.MALE)
    )
    await uow.commit()

    req = FilterPersonRequest(
        filters=PersonFilterRequestData(name="tree-a-only"),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    in_own_tree = await client.post(
        persons_url(uow.tree_id, "/list"),
        json=req.model_dump(mode="json"),
        headers=admin_headers,
    )
    assert in_own_tree.status_code == 200
    assert in_own_tree.json()["total"] >= 1

    in_other_tree = await client.post(
        persons_url(other_tree.safe_id, "/list"),
        json=req.model_dump(mode="json"),
        headers=admin_headers,
    )
    assert in_other_tree.status_code == 200
    assert in_other_tree.json()["total"] == 0
