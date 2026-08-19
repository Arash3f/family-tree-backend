import json
from datetime import date
from uuid import UUID

import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.auth.login_auth_login_post import (
    asyncio_detailed as login,
)
from family_tree_api_client.api.persons.create_person_family_trees_tree_id_persons_post import (  # noqa: E501
    asyncio_detailed as create_person,
)
from family_tree_api_client.api.persons.delete_person_family_trees_tree_id_persons_person_id_delete import (  # noqa: E501
    asyncio_detailed as delete_person,
)
from family_tree_api_client.api.persons.get_person_family_trees_tree_id_persons_person_id_get import (  # noqa: E501
    asyncio_detailed as get_person,
)
from family_tree_api_client.api.persons.get_person_list_by_filter_family_trees_tree_id_persons_list_post import (  # noqa: E501
    asyncio_detailed as get_person_list_by_filter,
)
from family_tree_api_client.api.persons.update_person_family_trees_tree_id_persons_put import (  # noqa: E501
    asyncio_detailed as update_person,
)
from family_tree_api_client.models.body_login_auth_login_post import (
    BodyLoginAuthLoginPost,
)
from family_tree_api_client.models.filter_person_request import FilterPersonRequest
from family_tree_api_client.models.gender import Gender as ApiGender
from family_tree_api_client.models.login_response import LoginResponse
from family_tree_api_client.models.paginated_response_person_model import (
    PaginatedResponsePersonModel,
)
from family_tree_api_client.models.pagination_request_params import (
    PaginationRequestParams,
)
from family_tree_api_client.models.parent_link_request import ParentLinkRequest
from family_tree_api_client.models.person_create_request import PersonCreateRequest
from family_tree_api_client.models.person_create_response import PersonCreateResponse
from family_tree_api_client.models.person_filter_request_data import (
    PersonFilterRequestData,
)
from family_tree_api_client.models.person_get_response import PersonGetResponse
from family_tree_api_client.models.person_sort_field import PersonSortField
from family_tree_api_client.models.person_update_date_request import (
    PersonUpdateDateRequest,
)
from family_tree_api_client.models.person_update_request import PersonUpdateRequest
from family_tree_api_client.models.person_update_response import PersonUpdateResponse
from family_tree_api_client.models.person_update_where_request import (
    PersonUpdateWhereRequest,
)
from family_tree_api_client.models.result_response import ResultResponse
from family_tree_api_client.models.sort_order_field import SortOrderField
from family_tree_api_client.models.sort_request_params_person_sort_field import (
    SortRequestParamsPersonSortField,
)
from httpx import ASGITransport, AsyncClient

from app.domain.entities.person import Gender, Person
from app.domain.entities.user import User
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_client as admin_client
from tests.e2e.auth_headers import member_client as member_client
from tests.helpers.uow import TreeUnitOfWork

# ============================================================
# CREATE PERSON
# ============================================================


@pytest.mark.asyncio
async def test_create_person_permission_denied(
    tree_id, member_client: AuthenticatedClient
):
    req = PersonCreateRequest(
        name="limited-person",
        gender=ApiGender.MALE,
    )
    resp = await create_person(tree_id=tree_id, client=member_client, body=req)

    assert resp.status_code == 403
    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_create_person_unauthenticated(client: Client, tree_id):
    req = PersonCreateRequest(
        name="limited-person",
        gender=ApiGender.MALE,
    )
    resp = await create_person(tree_id=tree_id, client=client, body=req)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_person_success(tree_id, admin_client: AuthenticatedClient, uow):
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
        gender=ApiGender.MALE,
        parents=[
            ParentLinkRequest(parent_id=father.safe_id),
            ParentLinkRequest(parent_id=mother.safe_id),
        ],
    )

    resp = await create_person(tree_id=tree_id, client=admin_client, body=req)

    assert resp.status_code == 200

    assert isinstance(resp.parsed, PersonCreateResponse)
    person_data = resp.parsed
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
async def test_get_person_permission_denied(
    tree_id, member_client: AuthenticatedClient
):
    resp = await get_person(
        tree_id=tree_id, person_id=UUID(int=1), client=member_client
    )

    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_get_person_unauthenticated(client: Client, tree_id):
    resp = await get_person(tree_id=tree_id, person_id=UUID(int=1), client=client)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_person_success(
    tree_id, admin_client: AuthenticatedClient, uow: TreeUnitOfWork
):
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

    resp = await get_person(
        tree_id=tree_id, person_id=person.safe_id, client=admin_client
    )

    assert resp.status_code == 200

    assert isinstance(resp.parsed, PersonGetResponse)
    data = resp.parsed
    assert data.id == person.safe_id
    assert data.name == person.name
    assert data.gender.value == person.gender.value
    assert data.birth_date == date(1990, 1, 1)
    assert data.parents == []
    assert not data.marriage_id


@pytest.mark.asyncio
async def test_get_person_with_invalid_id(tree_id, admin_client: AuthenticatedClient):
    resp = await get_person(
        tree_id=tree_id, person_id=UUID(int=999999), client=admin_client
    )

    assert resp.status_code == 404
    body = json.loads(resp.content)
    assert body["error_code"] == 1104
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERSON_NOT_FOUND]


# ============================================================
# UPDATE PERSON
# ============================================================


@pytest.mark.asyncio
async def test_update_person_permission_denied(
    tree_id, member_client: AuthenticatedClient
):
    payload = PersonUpdateRequest(
        where=PersonUpdateWhereRequest(person_id=UUID(int=1)),
        data=PersonUpdateDateRequest(name="updated"),
    )

    resp = await update_person(tree_id=tree_id, client=member_client, body=payload)

    assert resp.status_code == 403
    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_update_person_unauthenticated(client: Client, tree_id):
    payload = PersonUpdateRequest(
        where=PersonUpdateWhereRequest(person_id=UUID(int=1)),
        data=PersonUpdateDateRequest(name="updated"),
    )

    resp = await update_person(tree_id=tree_id, client=client, body=payload)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_person_success(
    tree_id, admin_client: AuthenticatedClient, uow: TreeUnitOfWork
):
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
        where=PersonUpdateWhereRequest(person_id=person.safe_id),
        data=PersonUpdateDateRequest(name="new-name", gender=ApiGender.FEMALE),
    )

    resp = await update_person(tree_id=tree_id, client=admin_client, body=payload)

    assert resp.status_code == 200
    assert isinstance(resp.parsed, PersonUpdateResponse)

    async with uow:
        updated = await uow.persons.get_or_raise(person_id=person.safe_id)

    assert updated.name == payload.data.name
    assert updated.gender.value == payload.data.gender.value


@pytest.mark.asyncio
async def test_update_person_with_invalid_id(
    tree_id, admin_client: AuthenticatedClient
):
    payload = PersonUpdateRequest(
        where=PersonUpdateWhereRequest(person_id=UUID(int=88888)),
        data=PersonUpdateDateRequest(name="new-name"),
    )

    resp = await update_person(tree_id=tree_id, client=admin_client, body=payload)

    assert resp.status_code == 404
    body = json.loads(resp.content)
    assert body["error_code"] == 1104
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERSON_NOT_FOUND]


# ============================================================
# DELETE PERSON
# ============================================================


@pytest.mark.asyncio
async def test_delete_person_permission_denied(
    tree_id, member_client: AuthenticatedClient
):
    resp = await delete_person(
        tree_id=tree_id, person_id=UUID(int=1), client=member_client
    )

    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_delete_person_unauthenticated(client: Client, tree_id):
    resp = await delete_person(tree_id=tree_id, person_id=UUID(int=1), client=client)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_person_success(
    tree_id, admin_client: AuthenticatedClient, uow: TreeUnitOfWork
):
    person = await uow.persons.create(
        Person(
            tree_id=uow.tree_id,
            id=None,
            name="to-delete",
            gender=Gender.MALE,
        )
    )
    await uow.commit()

    resp = await delete_person(
        tree_id=tree_id, person_id=person.safe_id, client=admin_client
    )

    assert resp.status_code == 200
    assert isinstance(resp.parsed, ResultResponse)

    deleted_person_id = person.safe_id
    async with uow:
        deleted = await uow.persons.get(person_id=deleted_person_id)

    assert deleted is None


@pytest.mark.asyncio
async def test_delete_person_with_invalid_id(
    tree_id, admin_client: AuthenticatedClient
):
    resp = await delete_person(
        tree_id=tree_id, person_id=UUID(int=999999), client=admin_client
    )

    assert resp.status_code == 404
    body = json.loads(resp.content)
    assert body["error_code"] == 1104
    assert body["status"] == 404
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERSON_NOT_FOUND]


# ============================================================
# LIST PERSONS
# ============================================================


def _person_sort_request() -> FilterPersonRequest:
    return FilterPersonRequest(
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParamsPersonSortField(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )


@pytest.mark.asyncio
async def test_get_person_list_by_filter_permission_denied(
    tree_id, member_client: AuthenticatedClient
):
    req = _person_sort_request()

    resp = await get_person_list_by_filter(
        tree_id=tree_id, client=member_client, body=req
    )

    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    assert body["status"] == 403
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.TREE_MEMBERSHIP_DENIED]


@pytest.mark.asyncio
async def test_get_person_list_by_filter_unauthenticated(client: Client, tree_id):
    req = _person_sort_request()

    resp = await get_person_list_by_filter(tree_id=tree_id, client=client, body=req)

    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_person_list_by_filter_success(
    tree_id,
    admin_client: AuthenticatedClient,
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
        sort=SortRequestParamsPersonSortField(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.ASC,
        ),
    )

    resp = await get_person_list_by_filter(
        tree_id=tree_id, client=admin_client, body=req
    )

    assert resp.status_code == 200

    assert isinstance(resp.parsed, PaginatedResponsePersonModel)
    data = resp.parsed
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


async def _reader_client(
    client: Client, uow, asgi_transport: ASGITransport
) -> tuple[AuthenticatedClient, User]:
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

    login_resp = await login(
        client=client,
        body=BodyLoginAuthLoginPost(username="person_reader", password="person_reader"),
    )
    assert login_resp.status_code == 200
    assert isinstance(login_resp.parsed, LoginResponse)
    token = login_resp.parsed.access_token

    async_httpx = AsyncClient(
        transport=asgi_transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {token}"},
    )
    reader_client = AuthenticatedClient(base_url="http://testserver", token=token)
    reader_client.set_async_httpx_client(async_httpx)
    return reader_client, reader


@pytest.mark.asyncio
async def test_list_persons_denied_for_non_member(
    client: Client, tree_id, uow, asgi_transport: ASGITransport
):
    reader_client, _reader = await _reader_client(client, uow, asgi_transport)

    req = _person_sort_request()

    resp = await get_person_list_by_filter(
        tree_id=tree_id, client=reader_client, body=req
    )

    assert resp.status_code == 403
    body = json.loads(resp.content)
    assert body["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_list_persons_allowed_for_member(
    client: Client, tree_id, uow, asgi_transport: ASGITransport
):
    reader_client, reader = await _reader_client(client, uow, asgi_transport)
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
        sort=SortRequestParamsPersonSortField(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    resp = await get_person_list_by_filter(
        tree_id=tree_id, client=reader_client, body=req
    )

    assert resp.status_code == 200
    assert isinstance(resp.parsed, PaginatedResponsePersonModel)
    data = resp.parsed
    assert data.total >= 1
    assert any(item.name == "member-visible" for item in data.items)


@pytest.mark.asyncio
async def test_person_lists_are_isolated_per_tree(
    admin_client: AuthenticatedClient, uow
):
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
        sort=SortRequestParamsPersonSortField(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    )

    in_own_tree = await get_person_list_by_filter(
        tree_id=uow.tree_id, client=admin_client, body=req
    )
    assert in_own_tree.status_code == 200
    assert isinstance(in_own_tree.parsed, PaginatedResponsePersonModel)
    assert in_own_tree.parsed.total >= 1

    in_other_tree = await get_person_list_by_filter(
        tree_id=other_tree.safe_id, client=admin_client, body=req
    )
    assert in_other_tree.status_code == 200
    assert isinstance(in_other_tree.parsed, PaginatedResponsePersonModel)
    assert in_other_tree.parsed.total == 0
