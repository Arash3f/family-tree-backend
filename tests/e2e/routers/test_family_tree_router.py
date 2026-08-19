import json
from uuid import uuid4

import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.family_trees.add_tree_member_family_trees_tree_id_members_post import (  # noqa: E501
    asyncio_detailed as add_tree_member_api,
)
from family_tree_api_client.api.family_trees.create_family_tree_family_trees_post import (  # noqa: E501
    asyncio_detailed as create_family_tree,
)
from family_tree_api_client.api.family_trees.delete_family_tree_family_trees_tree_id_delete import (  # noqa: E501
    asyncio_detailed as delete_family_tree,
)
from family_tree_api_client.api.family_trees.get_family_tree_family_trees_tree_id_get import (  # noqa: E501
    asyncio_detailed as get_family_tree,
)
from family_tree_api_client.api.family_trees.list_family_trees_family_trees_get import (
    asyncio_detailed as list_family_trees,
)
from family_tree_api_client.api.family_trees.list_tree_members_family_trees_tree_id_members_get import (  # noqa: E501
    asyncio_detailed as list_tree_members,
)
from family_tree_api_client.api.family_trees.remove_tree_member_family_trees_tree_id_members_user_id_delete import (  # noqa: E501
    asyncio_detailed as remove_tree_member,
)
from family_tree_api_client.api.family_trees.update_family_tree_family_trees_tree_id_patch import (  # noqa: E501
    asyncio_detailed as update_family_tree,
)
from family_tree_api_client.api.family_trees.update_tree_member_family_trees_tree_id_members_user_id_patch import (  # noqa: E501
    asyncio_detailed as update_tree_member,
)
from family_tree_api_client.api.persons.create_person_family_trees_tree_id_persons_post import (  # noqa: E501
    asyncio_detailed as create_person,
)
from family_tree_api_client.models.family_tree_create_request import (
    FamilyTreeCreateRequest,
)
from family_tree_api_client.models.family_tree_response import FamilyTreeResponse
from family_tree_api_client.models.family_tree_update_request import (
    FamilyTreeUpdateRequest,
)
from family_tree_api_client.models.gender import Gender as ApiGender
from family_tree_api_client.models.person_create_request import PersonCreateRequest
from family_tree_api_client.models.result_response import ResultResponse
from family_tree_api_client.models.tree_member_add_request import (
    TreeMemberAddRequest,
)
from family_tree_api_client.models.tree_member_update_request import (
    TreeMemberUpdateRequest,
)
from family_tree_api_client.models.tree_membership_response import (
    TreeMembershipResponse,
)

from app.domain.entities.family_tree import TreeMemberRole
from app.domain.shared.permissions import Permissions
from app.utils.error_codes import ErrorCode
from tests.e2e.auth_headers import admin_client as admin_client
from tests.helpers.auth import create_authenticated_user
from tests.helpers.family_tree import add_tree_member, create_family_tree_with_owner

ALL_TREE_PERMISSIONS = [
    Permissions.TREE_CREATE,
    Permissions.TREE_READ,
    Permissions.TREE_UPDATE,
    Permissions.TREE_DELETE,
]


def _error_code(response) -> int:
    return json.loads(response.content)["error_code"]


# ============================================================
# CREATE / READ
# ============================================================


@pytest.mark.asyncio
async def test_create_family_tree_makes_the_caller_owner(
    admin_client: AuthenticatedClient,
):
    resp = await create_family_tree(
        client=admin_client, body=FamilyTreeCreateRequest(name="Ancestors")
    )

    assert resp.status_code == 201
    assert isinstance(resp.parsed, FamilyTreeResponse)
    assert resp.parsed.name == "Ancestors"

    members = await list_tree_members(tree_id=resp.parsed.id, client=admin_client)
    assert members.status_code == 200
    roles = [m.role for m in members.parsed]
    assert roles == [TreeMemberRole.OWNER.value]


@pytest.mark.asyncio
async def test_create_family_tree_requires_permission(
    client: Client,
    uow,
    asgi_transport,
):
    outsider = await create_authenticated_user(
        client, uow, permissions=[], asgi_transport=asgi_transport
    )

    resp = await create_family_tree(
        client=outsider.client, body=FamilyTreeCreateRequest(name="Nope")
    )

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.PERMISSION_DENIED)


@pytest.mark.asyncio
async def test_list_family_trees_returns_only_the_callers_trees(
    client: Client, uow, asgi_transport
):
    """Membership, not existence, decides what a user sees in the tree list."""
    actor = await create_authenticated_user(
        client, uow, permissions=ALL_TREE_PERMISSIONS, asgi_transport=asgi_transport
    )
    mine = await create_family_tree_with_owner(uow, owner=actor.user, name="Mine")
    await create_family_tree_with_owner(uow, name="Someone Else's")
    await uow.commit()

    resp = await list_family_trees(client=actor.client)

    assert resp.status_code == 200
    names = {tree.name for tree in resp.parsed}
    assert names == {"Mine"}
    assert [tree.id for tree in resp.parsed] == [mine.safe_id]


@pytest.mark.asyncio
async def test_get_family_tree_denied_for_non_member(
    client: Client,
    tree_id,
    uow,
    asgi_transport,
):
    outsider = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_READ], asgi_transport=asgi_transport
    )

    resp = await get_family_tree(tree_id=tree_id, client=outsider.client)

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_get_family_tree_allowed_for_member(
    client: Client,
    tree_id,
    uow,
    asgi_transport,
):
    member = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_READ], asgi_transport=asgi_transport
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    await uow.commit()

    resp = await get_family_tree(tree_id=tree_id, client=member.client)

    assert resp.status_code == 200
    assert isinstance(resp.parsed, FamilyTreeResponse)
    assert resp.parsed.id == tree_id


@pytest.mark.asyncio
async def test_get_unknown_family_tree_returns_not_found(
    admin_client: AuthenticatedClient,
):
    resp = await get_family_tree(tree_id=uuid4(), client=admin_client)

    assert resp.status_code == 404
    assert _error_code(resp) == int(ErrorCode.FAMILY_TREE_NOT_FOUND)


# ============================================================
# UPDATE / DELETE (owner only)
# ============================================================


@pytest.mark.asyncio
async def test_owner_can_rename_the_tree(tree_id, admin_client: AuthenticatedClient):
    resp = await update_family_tree(
        tree_id=tree_id,
        client=admin_client,
        body=FamilyTreeUpdateRequest(name="Renamed"),
    )

    assert resp.status_code == 200
    assert isinstance(resp.parsed, FamilyTreeResponse)
    assert resp.parsed.name == "Renamed"


@pytest.mark.asyncio
async def test_plain_member_cannot_rename_the_tree(
    client: Client,
    tree_id,
    uow,
    asgi_transport,
):
    """Holding the RBAC permission is not enough; ownership of the tree is."""
    member = await create_authenticated_user(
        client,
        uow,
        permissions=[Permissions.TREE_UPDATE],
        asgi_transport=asgi_transport,
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    await uow.commit()

    resp = await update_family_tree(
        tree_id=tree_id,
        client=member.client,
        body=FamilyTreeUpdateRequest(name="Hijacked"),
    )

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_OWNER_REQUIRED)


@pytest.mark.asyncio
async def test_plain_member_cannot_delete_the_tree(
    client: Client,
    tree_id,
    uow,
    asgi_transport,
):
    member = await create_authenticated_user(
        client,
        uow,
        permissions=[Permissions.TREE_DELETE],
        asgi_transport=asgi_transport,
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    await uow.commit()

    resp = await delete_family_tree(tree_id=tree_id, client=member.client)

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_OWNER_REQUIRED)


@pytest.mark.asyncio
async def test_owner_can_delete_their_own_tree(client: Client, uow, asgi_transport):
    actor = await create_authenticated_user(
        client, uow, permissions=ALL_TREE_PERMISSIONS, asgi_transport=asgi_transport
    )
    tree = await create_family_tree_with_owner(uow, owner=actor.user, name="Temporary")
    await uow.commit()

    resp = await delete_family_tree(tree_id=tree.safe_id, client=actor.client)

    assert resp.status_code == 200
    assert isinstance(resp.parsed, ResultResponse)
    listing = await list_family_trees(client=actor.client)
    assert listing.parsed == []


# ============================================================
# MEMBERSHIP MANAGEMENT
# ============================================================


@pytest.mark.asyncio
async def test_owner_can_add_and_remove_a_member(
    tree_id, admin_client: AuthenticatedClient, client: Client, uow, asgi_transport
):
    newcomer = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_READ], asgi_transport=asgi_transport
    )

    added = await add_tree_member_api(
        tree_id=tree_id,
        client=admin_client,
        body=TreeMemberAddRequest(username=newcomer.username),
    )
    assert added.status_code == 201
    assert isinstance(added.parsed, TreeMembershipResponse)
    assert added.parsed.role == TreeMemberRole.MEMBER.value
    assert added.parsed.permissions == ["view"]

    visible = await get_family_tree(tree_id=tree_id, client=newcomer.client)
    assert visible.status_code == 200
    assert isinstance(visible.parsed, FamilyTreeResponse)
    assert visible.parsed.my_permissions == ["view"]

    removed = await remove_tree_member(
        tree_id=tree_id, user_id=newcomer.user.safe_id, client=admin_client
    )
    assert removed.status_code == 200

    after = await get_family_tree(tree_id=tree_id, client=newcomer.client)
    assert after.status_code == 403
    assert _error_code(after) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_owner_can_grant_operation_access(
    tree_id, admin_client: AuthenticatedClient, client: Client, uow, asgi_transport
):
    from app.domain.shared.tree_access import TreeAccessPermissions

    newcomer = await create_authenticated_user(
        client,
        uow,
        permissions=[Permissions.TREE_READ],
        asgi_transport=asgi_transport,
    )

    added = await add_tree_member_api(
        tree_id=tree_id,
        client=admin_client,
        body=TreeMemberAddRequest(
            username=newcomer.username,
            permissions=[TreeAccessPermissions.PERSON_UPDATE],
        ),
    )
    assert added.status_code == 201
    assert isinstance(added.parsed, TreeMembershipResponse)
    assert set(added.parsed.permissions) == {
        TreeAccessPermissions.VIEW,
        TreeAccessPermissions.PERSON_UPDATE,
        TreeAccessPermissions.VIEW_BIRTH_DATE,
        TreeAccessPermissions.VIEW_PHOTO,
    }

    updated = await update_tree_member(
        tree_id=tree_id,
        user_id=newcomer.user.safe_id,
        client=admin_client,
        body=TreeMemberUpdateRequest(
            permissions=[
                TreeAccessPermissions.PERSON_UPDATE,
                TreeAccessPermissions.PERSON_CREATE,
            ]
        ),
    )
    assert updated.status_code == 200
    assert isinstance(updated.parsed, TreeMembershipResponse)
    assert set(updated.parsed.permissions) == {
        TreeAccessPermissions.VIEW,
        TreeAccessPermissions.PERSON_UPDATE,
        TreeAccessPermissions.PERSON_CREATE,
        TreeAccessPermissions.VIEW_BIRTH_DATE,
        TreeAccessPermissions.VIEW_PHOTO,
    }

    me = await get_family_tree(tree_id=tree_id, client=newcomer.client)
    assert me.status_code == 200
    assert isinstance(me.parsed, FamilyTreeResponse)
    assert set(me.parsed.my_permissions) == {
        TreeAccessPermissions.VIEW,
        TreeAccessPermissions.PERSON_UPDATE,
        TreeAccessPermissions.PERSON_CREATE,
        TreeAccessPermissions.VIEW_BIRTH_DATE,
        TreeAccessPermissions.VIEW_PHOTO,
    }


@pytest.mark.asyncio
async def test_member_without_add_access_cannot_create_person(
    tree_id,
    admin_client: AuthenticatedClient,
    client: Client,
    uow,
    asgi_transport,
):
    from app.domain.shared.tree_access import TreeAccessPermissions

    member = await create_authenticated_user(
        client,
        uow,
        permissions=[],
        asgi_transport=asgi_transport,
    )
    await add_tree_member(
        uow,
        tree_id=tree_id,
        user_id=member.user.safe_id,
        permissions=[TreeAccessPermissions.VIEW],
    )
    await uow.commit()

    resp = await create_person(
        tree_id=tree_id,
        client=member.client,
        body=PersonCreateRequest(name="Blocked", gender=ApiGender.MALE),
    )
    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_ACCESS_DENIED)


@pytest.mark.asyncio
async def test_adding_the_same_member_twice_is_rejected(
    tree_id,
    admin_client: AuthenticatedClient,
    client: Client,
    uow,
    asgi_transport,
):
    newcomer = await create_authenticated_user(
        client, uow, permissions=[], asgi_transport=asgi_transport
    )
    body = TreeMemberAddRequest(username=newcomer.username)

    first = await add_tree_member_api(tree_id=tree_id, client=admin_client, body=body)
    assert first.status_code == 201

    second = await add_tree_member_api(tree_id=tree_id, client=admin_client, body=body)

    assert second.status_code == 409
    assert _error_code(second) == int(ErrorCode.TREE_MEMBER_ALREADY_EXISTS)


@pytest.mark.asyncio
async def test_plain_member_cannot_add_members(
    client: Client,
    tree_id,
    uow,
    asgi_transport,
):
    member = await create_authenticated_user(
        client, uow, permissions=[], asgi_transport=asgi_transport
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    outsider = await create_authenticated_user(
        client, uow, permissions=[], asgi_transport=asgi_transport
    )
    await uow.commit()

    resp = await add_tree_member_api(
        tree_id=tree_id,
        client=member.client,
        body=TreeMemberAddRequest(username=outsider.username),
    )

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_ACCESS_DENIED)


@pytest.mark.asyncio
async def test_removing_an_owner_is_rejected(
    tree_id, admin_client: AuthenticatedClient, uow
):
    """Owners cannot be removed through membership management."""
    from tests.helpers.family_tree import get_admin_user

    admin = await get_admin_user(uow)

    resp = await remove_tree_member(
        tree_id=tree_id, user_id=admin.safe_id, client=admin_client
    )

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_ACCESS_DENIED)


@pytest.mark.asyncio
async def test_listing_members_denied_for_non_member(
    client: Client,
    tree_id,
    uow,
    asgi_transport,
):
    outsider = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_READ], asgi_transport=asgi_transport
    )

    resp = await list_tree_members(tree_id=tree_id, client=outsider.client)

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
