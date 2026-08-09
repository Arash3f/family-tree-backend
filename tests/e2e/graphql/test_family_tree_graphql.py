from uuid import UUID

import pytest

from app.domain.entities.family_tree import TreeMemberRole
from app.domain.entities.person import Gender, Person
from app.domain.shared.permissions import Permissions
from app.utils.error_codes import ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.helpers.auth import create_authenticated_user
from tests.helpers.family_tree import (
    add_tree_member,
    create_family_tree_with_owner,
    get_admin_user,
)
from tests.helpers.uow import TreeUnitOfWork

GRAPHQL_URL = "/graphql"

ALL_TREE_PERMISSIONS = [
    Permissions.TREE_CREATE,
    Permissions.TREE_READ,
    Permissions.TREE_UPDATE,
    Permissions.TREE_DELETE,
    Permissions.TREE_MEMBER_ADD,
    Permissions.TREE_MEMBER_REMOVE,
]


async def gql(
    client,
    query: str,
    variables: dict | None = None,
    headers: dict | None = None,
):
    payload: dict[str, object] = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    return await client.post(GRAPHQL_URL, json=payload, headers=headers or {})


def first_error_code(response) -> int:
    return response.json()["errors"][0]["extensions"]["error_code"]


CREATE_TREE = """
mutation CreateTree($data: FamilyTreeCreateInput!) {
  createFamilyTree(data: $data) { id name ownerUserId }
}
"""

LIST_TREES = """
query { familyTrees { id name } }
"""

GET_TREE = """
query GetTree($treeId: UUID!) {
  familyTree(treeId: $treeId) { id name }
}
"""

UPDATE_TREE = """
mutation UpdateTree($treeId: UUID!, $data: FamilyTreeUpdateInput!) {
  updateFamilyTree(treeId: $treeId, data: $data) { id name }
}
"""

TREE_MEMBERS = """
query Members($treeId: UUID!) {
  treeMembers(treeId: $treeId) { userId role }
}
"""

ADD_MEMBER = """
mutation AddMember($treeId: UUID!, $data: TreeMemberAddInput!) {
  addTreeMember(treeId: $treeId, data: $data) { userId role }
}
"""

LIST_PERSONS = """
query Persons($treeId: UUID!) {
  persons(treeId: $treeId) { total items { id name } }
}
"""

GET_PERSON = """
query GetPerson($treeId: UUID!, $personId: UUID!) {
  person(treeId: $treeId, personId: $personId) { id name }
}
"""

CREATE_PERSON = """
mutation CreatePerson($treeId: UUID!, $data: PersonCreateInput!) {
  createPerson(treeId: $treeId, data: $data) { id name }
}
"""


async def _person_in(uow: TreeUnitOfWork, tree_id: UUID, name: str) -> Person:
    person = await uow.persons.create(
        Person(id=None, tree_id=tree_id, name=name, gender=Gender.MALE)
    )
    await uow.commit()
    return person


# ============================================================
# TREE CRUD OVER GRAPHQL
# ============================================================


@pytest.mark.asyncio
async def test_graphql_create_tree_makes_the_caller_owner(client, admin_headers):  # noqa: F811
    resp = await gql(
        client, CREATE_TREE, {"data": {"name": "GraphQL Tree"}}, headers=admin_headers
    )

    assert resp.status_code == 200
    created = resp.json()["data"]["createFamilyTree"]
    assert created["name"] == "GraphQL Tree"

    members = await gql(
        client, TREE_MEMBERS, {"treeId": created["id"]}, headers=admin_headers
    )
    roles = [m["role"] for m in members.json()["data"]["treeMembers"]]
    assert roles == [TreeMemberRole.OWNER.value.upper()]


@pytest.mark.asyncio
async def test_graphql_tree_list_is_scoped_to_the_caller(client, uow):
    actor = await create_authenticated_user(
        client, uow, permissions=ALL_TREE_PERMISSIONS
    )
    await create_family_tree_with_owner(uow, owner=actor.user, name="Visible")
    await create_family_tree_with_owner(uow, name="Invisible")
    await uow.commit()

    resp = await gql(client, LIST_TREES, headers=actor.headers)

    names = {tree["name"] for tree in resp.json()["data"]["familyTrees"]}
    assert names == {"Visible"}


@pytest.mark.asyncio
async def test_graphql_get_tree_denied_for_non_member(client, tree_id, uow):
    outsider = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_READ]
    )

    resp = await gql(
        client, GET_TREE, {"treeId": str(tree_id)}, headers=outsider.headers
    )

    assert first_error_code(resp) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_graphql_plain_member_cannot_rename_a_tree(client, tree_id, uow):
    member = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_UPDATE, Permissions.TREE_READ]
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    await uow.commit()

    resp = await gql(
        client,
        UPDATE_TREE,
        {"treeId": str(tree_id), "data": {"name": "Hijacked"}},
        headers=member.headers,
    )

    assert first_error_code(resp) == int(ErrorCode.TREE_OWNER_REQUIRED)


@pytest.mark.asyncio
async def test_graphql_plain_member_cannot_add_members(client, tree_id, uow):
    member = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_MEMBER_ADD]
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    outsider = await create_authenticated_user(client, uow, permissions=[])
    await uow.commit()

    resp = await gql(
        client,
        ADD_MEMBER,
        {"treeId": str(tree_id), "data": {"userId": str(outsider.user.safe_id)}},
        headers=member.headers,
    )

    assert first_error_code(resp) == int(ErrorCode.TREE_OWNER_REQUIRED)


# ============================================================
# CROSS-TREE ISOLATION OVER GRAPHQL
# ============================================================


@pytest.mark.asyncio
async def test_graphql_non_member_cannot_list_persons(client, tree_id, uow):
    outsider = await create_authenticated_user(
        client, uow, permissions=[Permissions.PERSON_READ]
    )
    await _person_in(uow, tree_id, "hidden")

    resp = await gql(
        client, LIST_PERSONS, {"treeId": str(tree_id)}, headers=outsider.headers
    )

    assert first_error_code(resp) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_graphql_non_member_cannot_create_a_person(client, tree_id, uow):
    outsider = await create_authenticated_user(
        client, uow, permissions=[Permissions.PERSON_CREATE]
    )

    resp = await gql(
        client,
        CREATE_PERSON,
        {"treeId": str(tree_id), "data": {"name": "intruder", "gender": "MALE"}},
        headers=outsider.headers,
    )

    assert first_error_code(resp) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_graphql_member_of_one_tree_cannot_read_another(client, tree_id, uow):
    actor = await create_authenticated_user(
        client, uow, permissions=[Permissions.PERSON_READ]
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=actor.user.safe_id)
    other_tree = await create_family_tree_with_owner(uow, name="Foreign Tree")
    await uow.commit()
    await _person_in(uow, other_tree.safe_id, "foreign-person")

    resp = await gql(
        client,
        LIST_PERSONS,
        {"treeId": str(other_tree.safe_id)},
        headers=actor.headers,
    )

    assert first_error_code(resp) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_graphql_person_lookup_respects_the_tree_in_the_query(
    client,
    tree_id,
    uow,
    admin_headers,  # noqa: F811
):
    """Being a member of both trees still does not merge their contents."""
    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Admin's Second Tree"
    )
    await uow.commit()
    foreigner = await _person_in(uow, other_tree.safe_id, "belongs-elsewhere")

    resp = await gql(
        client,
        GET_PERSON,
        {"treeId": str(tree_id), "personId": str(foreigner.safe_id)},
        headers=admin_headers,
    )

    assert first_error_code(resp) == int(ErrorCode.PERSON_TREE_MISMATCH)
