from uuid import UUID

import pytest
from family_tree_graphql_client import FamilyTreeGraphQLClient
from family_tree_graphql_client.enums import Gender as ApiGender
from family_tree_graphql_client.enums import TreeMemberRole as ApiTreeMemberRole
from family_tree_graphql_client.exceptions import GraphQLClientGraphQLMultiError
from family_tree_graphql_client.input_types import (
    FamilyTreeCreateInput,
    FamilyTreeUpdateInput,
    PersonCreateInput,
    TreeMemberAddInput,
)

from app.domain.entities.family_tree import TreeMemberRole
from app.domain.entities.person import Gender, Person
from app.domain.shared.permissions import Permissions
from app.utils.error_codes import ErrorCode
from tests.e2e.graphql.graphql_auth import admin_gql_client as admin_gql_client
from tests.e2e.graphql.graphql_auth import gql_client_with_headers
from tests.e2e.graphql.legacy_auth import create_authenticated_user
from tests.helpers.family_tree import (
    add_tree_member,
    create_family_tree_with_owner,
    get_admin_user,
)
from tests.helpers.uow import TreeUnitOfWork

ALL_TREE_PERMISSIONS = [
    Permissions.TREE_CREATE,
    Permissions.TREE_READ,
    Permissions.TREE_UPDATE,
    Permissions.TREE_DELETE,
]


def first_error_code(exc_info: pytest.ExceptionInfo) -> int:
    return exc_info.value.errors[0].extensions["error_code"]


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
async def test_graphql_create_tree_makes_the_caller_owner(
    admin_gql_client: FamilyTreeGraphQLClient,
):
    created = await admin_gql_client.create_tree(
        data=FamilyTreeCreateInput(name="GraphQL Tree")
    )
    tree = created.create_family_tree
    assert tree.name == "GraphQL Tree"

    members = await admin_gql_client.tree_members(tree_id=tree.id)
    roles = [m.role for m in members.tree_members]
    assert roles == [ApiTreeMemberRole(TreeMemberRole.OWNER.value.upper())]


@pytest.mark.asyncio
async def test_graphql_tree_list_is_scoped_to_the_caller(client, uow, asgi_transport):
    actor = await create_authenticated_user(
        client, uow, permissions=ALL_TREE_PERMISSIONS
    )
    await create_family_tree_with_owner(uow, owner=actor.user, name="Visible")
    await create_family_tree_with_owner(uow, name="Invisible")
    await uow.commit()

    actor_client = gql_client_with_headers(asgi_transport, actor.headers)
    resp = await actor_client.list_trees()

    names = {tree.name for tree in resp.family_trees}
    assert names == {"Visible"}


@pytest.mark.asyncio
async def test_graphql_get_tree_denied_for_non_member(
    client, tree_id, uow, asgi_transport
):
    outsider = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_READ]
    )
    outsider_client = gql_client_with_headers(asgi_transport, outsider.headers)

    with pytest.raises(GraphQLClientGraphQLMultiError) as exc_info:
        await outsider_client.get_tree(tree_id=tree_id)

    assert first_error_code(exc_info) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_graphql_plain_member_cannot_rename_a_tree(
    client, tree_id, uow, asgi_transport
):
    member = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_UPDATE, Permissions.TREE_READ]
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    await uow.commit()
    member_client = gql_client_with_headers(asgi_transport, member.headers)

    with pytest.raises(GraphQLClientGraphQLMultiError) as exc_info:
        await member_client.update_tree(
            tree_id=tree_id, data=FamilyTreeUpdateInput(name="Hijacked")
        )

    assert first_error_code(exc_info) == int(ErrorCode.TREE_OWNER_REQUIRED)


@pytest.mark.asyncio
async def test_graphql_plain_member_cannot_add_members(
    client, tree_id, uow, asgi_transport
):
    member = await create_authenticated_user(client, uow, permissions=[])
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    outsider = await create_authenticated_user(client, uow, permissions=[])
    await uow.commit()
    member_client = gql_client_with_headers(asgi_transport, member.headers)

    with pytest.raises(GraphQLClientGraphQLMultiError) as exc_info:
        await member_client.add_member(
            tree_id=tree_id,
            data=TreeMemberAddInput(username=outsider.username),
        )

    assert first_error_code(exc_info) == int(ErrorCode.TREE_ACCESS_DENIED)


# ============================================================
# CROSS-TREE ISOLATION OVER GRAPHQL
# ============================================================


@pytest.mark.asyncio
async def test_graphql_non_member_cannot_list_persons(
    client, tree_id, uow, asgi_transport
):
    outsider = await create_authenticated_user(client, uow, permissions=[])
    await _person_in(uow, tree_id, "hidden")
    outsider_client = gql_client_with_headers(asgi_transport, outsider.headers)

    with pytest.raises(GraphQLClientGraphQLMultiError) as exc_info:
        await outsider_client.list_persons(tree_id=tree_id)

    assert first_error_code(exc_info) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_graphql_non_member_cannot_create_a_person(
    client, tree_id, uow, asgi_transport
):
    outsider = await create_authenticated_user(client, uow, permissions=[])
    outsider_client = gql_client_with_headers(asgi_transport, outsider.headers)

    with pytest.raises(GraphQLClientGraphQLMultiError) as exc_info:
        await outsider_client.create_person(
            tree_id=tree_id,
            data=PersonCreateInput(name="intruder", gender=ApiGender.MALE),
        )

    assert first_error_code(exc_info) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_graphql_member_of_one_tree_cannot_read_another(
    client, tree_id, uow, asgi_transport
):
    actor = await create_authenticated_user(client, uow, permissions=[])
    await add_tree_member(uow, tree_id=tree_id, user_id=actor.user.safe_id)
    other_tree = await create_family_tree_with_owner(uow, name="Foreign Tree")
    await uow.commit()
    await _person_in(uow, other_tree.safe_id, "foreign-person")
    actor_client = gql_client_with_headers(asgi_transport, actor.headers)

    with pytest.raises(GraphQLClientGraphQLMultiError) as exc_info:
        await actor_client.list_persons(tree_id=other_tree.safe_id)

    assert first_error_code(exc_info) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_graphql_person_lookup_respects_the_tree_in_the_query(
    tree_id,
    uow,
    admin_gql_client: FamilyTreeGraphQLClient,
):
    """Being a member of both trees still does not merge their contents."""
    admin = await get_admin_user(uow)
    other_tree = await create_family_tree_with_owner(
        uow, owner=admin, name="Admin's Second Tree"
    )
    await uow.commit()
    foreigner = await _person_in(uow, other_tree.safe_id, "belongs-elsewhere")

    with pytest.raises(GraphQLClientGraphQLMultiError) as exc_info:
        await admin_gql_client.get_person(tree_id=tree_id, person_id=foreigner.safe_id)

    assert first_error_code(exc_info) == int(ErrorCode.PERSON_TREE_MISMATCH)
