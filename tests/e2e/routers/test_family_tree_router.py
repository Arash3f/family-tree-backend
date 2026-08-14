import pytest

from app.domain.entities.family_tree import TreeMemberRole
from app.domain.shared.permissions import Permissions
from app.utils.error_codes import ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.helpers.auth import create_authenticated_user
from tests.helpers.family_tree import add_tree_member, create_family_tree_with_owner

TREES_URL = "/family-trees"

ALL_TREE_PERMISSIONS = [
    Permissions.TREE_CREATE,
    Permissions.TREE_READ,
    Permissions.TREE_UPDATE,
    Permissions.TREE_DELETE,
    Permissions.TREE_MEMBER_ADD,
    Permissions.TREE_MEMBER_REMOVE,
]


def _error_code(response) -> int:
    return response.json()["error_code"]


# ============================================================
# CREATE / READ
# ============================================================


@pytest.mark.asyncio
async def test_create_family_tree_makes_the_caller_owner(client, admin_headers):  # noqa: F811
    resp = await client.post(
        TREES_URL, json={"name": "Ancestors"}, headers=admin_headers
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Ancestors"

    members = await client.get(
        f"/family-trees/{body['id']}/members", headers=admin_headers
    )
    assert members.status_code == 200
    roles = [m["role"] for m in members.json()]
    assert roles == [TreeMemberRole.OWNER.value]


@pytest.mark.asyncio
async def test_create_family_tree_requires_permission(client, uow):
    outsider = await create_authenticated_user(client, uow, permissions=[])

    resp = await client.post(TREES_URL, json={"name": "Nope"}, headers=outsider.headers)

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.PERMISSION_DENIED)


@pytest.mark.asyncio
async def test_list_family_trees_returns_only_the_callers_trees(client, uow):
    """Membership, not existence, decides what a user sees in the tree list."""
    actor = await create_authenticated_user(
        client, uow, permissions=ALL_TREE_PERMISSIONS
    )
    mine = await create_family_tree_with_owner(uow, owner=actor.user, name="Mine")
    await create_family_tree_with_owner(uow, name="Someone Else's")
    await uow.commit()

    resp = await client.get(TREES_URL, headers=actor.headers)

    assert resp.status_code == 200
    names = {tree["name"] for tree in resp.json()}
    assert names == {"Mine"}
    assert [tree["id"] for tree in resp.json()] == [str(mine.safe_id)]


@pytest.mark.asyncio
async def test_get_family_tree_denied_for_non_member(client, tree_id, uow):
    outsider = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_READ]
    )

    resp = await client.get(f"/family-trees/{tree_id}", headers=outsider.headers)

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_get_family_tree_allowed_for_member(client, tree_id, uow):
    member = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_READ]
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    await uow.commit()

    resp = await client.get(f"/family-trees/{tree_id}", headers=member.headers)

    assert resp.status_code == 200
    assert resp.json()["id"] == str(tree_id)


@pytest.mark.asyncio
async def test_get_unknown_family_tree_returns_not_found(client, admin_headers):  # noqa: F811
    from uuid import uuid4

    resp = await client.get(f"/family-trees/{uuid4()}", headers=admin_headers)

    assert resp.status_code == 404
    assert _error_code(resp) == int(ErrorCode.FAMILY_TREE_NOT_FOUND)


# ============================================================
# UPDATE / DELETE (owner only)
# ============================================================


@pytest.mark.asyncio
async def test_owner_can_rename_the_tree(client, tree_id, admin_headers):  # noqa: F811
    resp = await client.patch(
        f"/family-trees/{tree_id}", json={"name": "Renamed"}, headers=admin_headers
    )

    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


@pytest.mark.asyncio
async def test_plain_member_cannot_rename_the_tree(client, tree_id, uow):
    """Holding the RBAC permission is not enough; ownership of the tree is."""
    member = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_UPDATE]
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    await uow.commit()

    resp = await client.patch(
        f"/family-trees/{tree_id}", json={"name": "Hijacked"}, headers=member.headers
    )

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_OWNER_REQUIRED)


@pytest.mark.asyncio
async def test_plain_member_cannot_delete_the_tree(client, tree_id, uow):
    member = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_DELETE]
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    await uow.commit()

    resp = await client.delete(f"/family-trees/{tree_id}", headers=member.headers)

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_OWNER_REQUIRED)


@pytest.mark.asyncio
async def test_owner_can_delete_their_own_tree(client, uow):
    actor = await create_authenticated_user(
        client, uow, permissions=ALL_TREE_PERMISSIONS
    )
    tree = await create_family_tree_with_owner(uow, owner=actor.user, name="Temporary")
    await uow.commit()

    resp = await client.delete(f"/family-trees/{tree.safe_id}", headers=actor.headers)

    assert resp.status_code == 200
    listing = await client.get(TREES_URL, headers=actor.headers)
    assert listing.json() == []


# ============================================================
# MEMBERSHIP MANAGEMENT
# ============================================================


@pytest.mark.asyncio
async def test_owner_can_add_and_remove_a_member(client, tree_id, admin_headers, uow):  # noqa: F811
    newcomer = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_READ]
    )

    added = await client.post(
        f"/family-trees/{tree_id}/members",
        json={"username": newcomer.username},
        headers=admin_headers,
    )
    assert added.status_code == 201
    assert added.json()["role"] == TreeMemberRole.MEMBER.value
    assert added.json()["permissions"] == ["view"]

    visible = await client.get(f"/family-trees/{tree_id}", headers=newcomer.headers)
    assert visible.status_code == 200
    assert visible.json()["my_permissions"] == ["view"]

    removed = await client.delete(
        f"/family-trees/{tree_id}/members/{newcomer.user.safe_id}",
        headers=admin_headers,
    )
    assert removed.status_code == 200

    after = await client.get(f"/family-trees/{tree_id}", headers=newcomer.headers)
    assert after.status_code == 403
    assert _error_code(after) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)


@pytest.mark.asyncio
async def test_owner_can_grant_edit_and_add_access(client, tree_id, admin_headers, uow):  # noqa: F811
    from app.domain.shared.tree_access import TreeAccessPermissions

    newcomer = await create_authenticated_user(
        client,
        uow,
        permissions=[
            Permissions.TREE_READ,
            Permissions.PERSON_READ,
            Permissions.PERSON_CREATE,
            Permissions.PERSON_UPDATE,
        ],
    )

    added = await client.post(
        f"/family-trees/{tree_id}/members",
        json={
            "username": newcomer.username,
            "permissions": [TreeAccessPermissions.EDIT],
        },
        headers=admin_headers,
    )
    assert added.status_code == 201
    assert set(added.json()["permissions"]) == {
        TreeAccessPermissions.VIEW,
        TreeAccessPermissions.EDIT,
    }

    updated = await client.patch(
        f"/family-trees/{tree_id}/members/{newcomer.user.safe_id}",
        json={
            "permissions": [
                TreeAccessPermissions.EDIT,
                TreeAccessPermissions.ADD_PERSONS,
            ]
        },
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert set(updated.json()["permissions"]) == {
        TreeAccessPermissions.VIEW,
        TreeAccessPermissions.EDIT,
        TreeAccessPermissions.ADD_PERSONS,
    }

    me = await client.get(f"/family-trees/{tree_id}", headers=newcomer.headers)
    assert me.status_code == 200
    assert set(me.json()["my_permissions"]) == {
        TreeAccessPermissions.VIEW,
        TreeAccessPermissions.EDIT,
        TreeAccessPermissions.ADD_PERSONS,
    }


@pytest.mark.asyncio
async def test_member_without_add_access_cannot_create_person(
    client,
    tree_id,
    admin_headers,
    uow,  # noqa: F811
):
    from app.domain.shared.tree_access import TreeAccessPermissions

    member = await create_authenticated_user(
        client,
        uow,
        permissions=[Permissions.PERSON_CREATE, Permissions.PERSON_READ],
    )
    await add_tree_member(
        uow,
        tree_id=tree_id,
        user_id=member.user.safe_id,
        permissions=[TreeAccessPermissions.VIEW],
    )
    await uow.commit()

    resp = await client.post(
        f"/family-trees/{tree_id}/persons",
        json={"name": "Blocked", "gender": "male"},
        headers=member.headers,
    )
    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_ACCESS_DENIED)


@pytest.mark.asyncio
async def test_adding_the_same_member_twice_is_rejected(
    client,
    tree_id,
    admin_headers,  # noqa: F811
    uow,
):
    newcomer = await create_authenticated_user(client, uow, permissions=[])
    payload = {"username": newcomer.username}

    first = await client.post(
        f"/family-trees/{tree_id}/members", json=payload, headers=admin_headers
    )
    assert first.status_code == 201

    second = await client.post(
        f"/family-trees/{tree_id}/members", json=payload, headers=admin_headers
    )

    assert second.status_code == 409
    assert _error_code(second) == int(ErrorCode.TREE_MEMBER_ALREADY_EXISTS)


@pytest.mark.asyncio
async def test_plain_member_cannot_add_members(client, tree_id, uow):
    member = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_MEMBER_ADD]
    )
    await add_tree_member(uow, tree_id=tree_id, user_id=member.user.safe_id)
    outsider = await create_authenticated_user(client, uow, permissions=[])
    await uow.commit()

    resp = await client.post(
        f"/family-trees/{tree_id}/members",
        json={"username": outsider.username},
        headers=member.headers,
    )

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_OWNER_REQUIRED)


@pytest.mark.asyncio
async def test_removing_the_last_owner_is_rejected(client, tree_id, admin_headers, uow):  # noqa: F811
    """A tree without an owner could never be administered again."""
    from tests.helpers.family_tree import get_admin_user

    admin = await get_admin_user(uow)

    resp = await client.delete(
        f"/family-trees/{tree_id}/members/{admin.safe_id}", headers=admin_headers
    )

    assert resp.status_code == 422
    assert _error_code(resp) == int(ErrorCode.CANNOT_REMOVE_LAST_OWNER)


@pytest.mark.asyncio
async def test_listing_members_denied_for_non_member(client, tree_id, uow):
    outsider = await create_authenticated_user(
        client, uow, permissions=[Permissions.TREE_READ]
    )

    resp = await client.get(
        f"/family-trees/{tree_id}/members", headers=outsider.headers
    )

    assert resp.status_code == 403
    assert _error_code(resp) == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
