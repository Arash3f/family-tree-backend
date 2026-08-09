from datetime import date
from uuid import UUID

import pytest

from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Gender, Person
from app.domain.shared.dto.person_filter_dto import PersonSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.domain.shared.permissions import Permissions
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    SortRequestParams,
)
from app.presentation.rest.schemas.dto.person_schema import (
    FilterPersonRequest,
    PersonCreateRequest,
    PersonFilterRequestData,
    PersonUpdateRequest,
    _PersonUpdateDateRequest,
    _PersonUpdateWhereRequest,
)
from app.utils.error_codes import ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.helpers.auth import AuthenticatedUser, create_authenticated_user
from tests.helpers.family_tree import add_tree_member, create_family_tree_with_owner
from tests.helpers.uow import TreeUnitOfWork

PERSON_PERMISSIONS = [
    Permissions.PERSON_CREATE,
    Permissions.PERSON_READ,
    Permissions.PERSON_UPDATE,
    Permissions.PERSON_DELETE,
]
MARRIAGE_PERMISSIONS = [
    Permissions.MARRIAGE_CREATE,
    Permissions.MARRIAGE_READ,
    Permissions.MARRIAGE_UPDATE,
    Permissions.MARRIAGE_DELETE,
    Permissions.MARRIAGE_DIVORCE,
]


def persons_url(tree_id: UUID, suffix: str = "") -> str:
    return f"/family-trees/{tree_id}/persons{suffix}"


def marriages_url(tree_id: UUID, suffix: str = "") -> str:
    return f"/family-trees/{tree_id}/marriages{suffix}"


def _list_request() -> dict:
    return FilterPersonRequest(
        filters=PersonFilterRequestData(),
        pagination=PaginationRequestParams(offset=0, page=1, page_size=30),
        sort=SortRequestParams(
            sort_by=PersonSortField.ID,
            sort_order=SortOrderField.DESC,
        ),
    ).model_dump(mode="json")


async def _person_in(uow: TreeUnitOfWork, tree_id: UUID, name: str) -> Person:
    person = await uow.persons.create(
        Person(id=None, tree_id=tree_id, name=name, gender=Gender.MALE)
    )
    await uow.commit()
    return person


async def _outsider(client, uow, permissions: list[str]) -> AuthenticatedUser:
    """A fully permissioned user who belongs to no tree at all."""
    return await create_authenticated_user(client, uow, permissions=permissions)


# ============================================================
# NON-MEMBERS ARE LOCKED OUT OF EVERY TREE-SCOPED ROUTE
# ============================================================


@pytest.mark.asyncio
async def test_non_member_cannot_read_persons_of_a_tree(client, tree_id, uow):
    outsider = await _outsider(client, uow, PERSON_PERMISSIONS)
    person = await _person_in(uow, tree_id, "hidden")

    responses = {
        "list": await client.post(
            persons_url(tree_id, "/list"),
            json=_list_request(),
            headers=outsider.headers,
        ),
        "get": await client.get(
            persons_url(tree_id, f"/{person.safe_id}"), headers=outsider.headers
        ),
    }

    for name, resp in responses.items():
        assert resp.status_code == 403, name
        assert resp.json()["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED), name


@pytest.mark.asyncio
async def test_non_member_cannot_write_persons_of_a_tree(client, tree_id, uow):
    """Read denial is worth little if the write paths stay open."""
    outsider = await _outsider(client, uow, PERSON_PERMISSIONS)
    person = await _person_in(uow, tree_id, "untouchable")

    create = await client.post(
        persons_url(tree_id, "/"),
        json=PersonCreateRequest(name="intruder", gender=Gender.MALE).model_dump(
            mode="json"
        ),
        headers=outsider.headers,
    )
    update = await client.put(
        persons_url(tree_id, "/"),
        json=PersonUpdateRequest(
            data=_PersonUpdateDateRequest(name="renamed-by-intruder"),
            where=_PersonUpdateWhereRequest(person_id=person.safe_id),
        ).model_dump(mode="json"),
        headers=outsider.headers,
    )
    delete = await client.delete(
        persons_url(tree_id, f"/{person.safe_id}"), headers=outsider.headers
    )

    for resp in (create, update, delete):
        assert resp.status_code == 403
        assert resp.json()["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)

    unchanged = await uow.persons.get(person.safe_id)
    assert unchanged is not None
    assert unchanged.name == "untouchable"


@pytest.mark.asyncio
async def test_non_member_cannot_reach_marriages_of_a_tree(client, tree_id, uow):
    outsider = await _outsider(client, uow, MARRIAGE_PERMISSIONS)

    resp = await client.post(
        marriages_url(tree_id, "/"),
        json={
            "spouse_a_id": str(UUID(int=1)),
            "spouse_b_id": str(UUID(int=2)),
            "married_at": "2020-01-01",
        },
        headers=outsider.headers,
    )

    assert resp.status_code == 403
    assert resp.json()["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_non_member_cannot_query_closest_relationship(client, tree_id, uow):
    outsider = await _outsider(client, uow, PERSON_PERMISSIONS)
    a = await _person_in(uow, tree_id, "path-a")
    b = await _person_in(uow, tree_id, "path-b")

    resp = await client.get(
        persons_url(tree_id, f"/{a.safe_id}/relation/{b.safe_id}"),
        headers=outsider.headers,
    )

    assert resp.status_code == 403
    assert resp.json()["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


# ============================================================
# MEMBERSHIP IN ONE TREE DOES NOT REACH INTO ANOTHER
# ============================================================


@pytest.mark.asyncio
async def test_member_of_one_tree_cannot_touch_another_tree(client, tree_id, uow):
    actor = await create_authenticated_user(client, uow, permissions=PERSON_PERMISSIONS)
    await add_tree_member(uow, tree_id=tree_id, user_id=actor.user.safe_id)
    other_tree = await create_family_tree_with_owner(uow, name="Foreign Tree")
    await uow.commit()
    foreigner = await _person_in(uow, other_tree.safe_id, "foreign-person")

    listing = await client.post(
        persons_url(other_tree.safe_id, "/list"),
        json=_list_request(),
        headers=actor.headers,
    )
    fetch = await client.get(
        persons_url(other_tree.safe_id, f"/{foreigner.safe_id}"),
        headers=actor.headers,
    )

    for resp in (listing, fetch):
        assert resp.status_code == 403
        assert resp.json()["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_person_from_another_tree_is_invisible_through_your_own_tree(
    client,
    tree_id,
    uow,
    admin_headers,  # noqa: F811
):
    """The tree in the URL must own the record, even for a member of both trees."""
    from tests.helpers.family_tree import get_admin_user

    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Admin's Second Tree"
    )
    await uow.commit()
    foreigner = await _person_in(uow, other_tree.safe_id, "belongs-elsewhere")

    resp = await client.get(
        persons_url(tree_id, f"/{foreigner.safe_id}"), headers=admin_headers
    )

    assert resp.status_code == 404
    assert resp.json()["error_code"] == int(ErrorCode.PERSON_TREE_MISMATCH)


@pytest.mark.asyncio
async def test_person_from_another_tree_cannot_be_updated_through_your_own_tree(
    client,
    tree_id,
    uow,
    admin_headers,  # noqa: F811
):
    from tests.helpers.family_tree import get_admin_user

    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Admin's Second Tree"
    )
    await uow.commit()
    foreigner = await _person_in(uow, other_tree.safe_id, "stable-name")

    resp = await client.put(
        persons_url(tree_id, "/"),
        json=PersonUpdateRequest(
            data=_PersonUpdateDateRequest(name="crossed-over"),
            where=_PersonUpdateWhereRequest(person_id=foreigner.safe_id),
        ).model_dump(mode="json"),
        headers=admin_headers,
    )

    assert resp.status_code == 404
    assert resp.json()["error_code"] == int(ErrorCode.PERSON_TREE_MISMATCH)

    unchanged = await uow.persons.get(foreigner.safe_id)
    assert unchanged is not None
    assert unchanged.name == "stable-name"


@pytest.mark.asyncio
async def test_marriage_from_another_tree_is_invisible_through_your_own_tree(
    client,
    tree_id,
    uow,
    admin_headers,  # noqa: F811
):
    from tests.helpers.family_tree import get_admin_user

    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Admin's Second Tree"
    )
    await uow.commit()

    husband = await uow.persons.create(
        Person(
            id=None,
            tree_id=other_tree.safe_id,
            name="foreign-husband",
            gender=Gender.MALE,
            birth_date=date(1980, 1, 1),
        )
    )
    wife = await uow.persons.create(
        Person(
            id=None,
            tree_id=other_tree.safe_id,
            name="foreign-wife",
            gender=Gender.FEMALE,
            birth_date=date(1982, 1, 1),
        )
    )
    marriage = await uow.marriages.create(
        Marriage(
            id=None,
            tree_id=other_tree.safe_id,
            spouse_a_id=husband.safe_id,
            spouse_b_id=wife.safe_id,
            married_at=date(2005, 1, 1),
        )
    )
    await uow.commit()

    resp = await client.get(
        marriages_url(tree_id, f"/{marriage.safe_id}"), headers=admin_headers
    )

    assert resp.status_code in (404, 422)
    assert resp.json()["error_code"] == int(ErrorCode.MARRIAGE_TREE_MISMATCH)


@pytest.mark.asyncio
async def test_person_lists_do_not_bleed_between_trees(
    client,
    tree_id,
    uow,
    admin_headers,  # noqa: F811
):
    from tests.helpers.family_tree import get_admin_user

    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Admin's Second Tree"
    )
    await uow.commit()
    await _person_in(uow, tree_id, "in-tree-a")
    await _person_in(uow, other_tree.safe_id, "in-tree-b")

    tree_a = await client.post(
        persons_url(tree_id, "/list"), json=_list_request(), headers=admin_headers
    )
    tree_b = await client.post(
        persons_url(other_tree.safe_id, "/list"),
        json=_list_request(),
        headers=admin_headers,
    )

    names_a = {item["name"] for item in tree_a.json()["items"]}
    names_b = {item["name"] for item in tree_b.json()["items"]}
    assert "in-tree-a" in names_a and "in-tree-b" not in names_a
    assert "in-tree-b" in names_b and "in-tree-a" not in names_b
