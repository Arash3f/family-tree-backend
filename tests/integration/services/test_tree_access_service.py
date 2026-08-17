import pytest

from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.family_tree import TreeMemberRole
from app.domain.exceptions.family_tree_exceptions import (
    TreeAccessDeniedException,
    TreeMembershipDeniedException,
    TreeOwnerRequiredException,
)
from app.domain.shared.tree_access import TreeAccessPermissions
from tests.helpers.family_tree import (
    add_tree_member,
    create_family_tree_with_owner,
)


@pytest.mark.asyncio
async def test_require_member_allows_owner(uow):
    tree = await create_family_tree_with_owner(uow)
    access = TreeAccessService(uow)
    membership = await access.require_member(
        tree_id=tree.safe_id, user_id=tree.owner_user_id
    )
    assert membership.is_owner()
    assert membership.has_access(TreeAccessPermissions.PERSON_UPDATE)


@pytest.mark.asyncio
async def test_require_member_denies_outsider(uow):
    tree = await create_family_tree_with_owner(uow)
    outsider = await create_family_tree_with_owner(uow)
    access = TreeAccessService(uow)
    with pytest.raises(TreeMembershipDeniedException):
        await access.require_member(
            tree_id=tree.safe_id, user_id=outsider.owner_user_id
        )


@pytest.mark.asyncio
async def test_require_owner_rejects_member(uow):
    tree = await create_family_tree_with_owner(uow)
    member_tree = await create_family_tree_with_owner(uow)
    member_user_id = member_tree.owner_user_id
    await add_tree_member(
        uow,
        tree_id=tree.safe_id,
        user_id=member_user_id,
        role=TreeMemberRole.MEMBER,
    )
    access = TreeAccessService(uow)
    with pytest.raises(TreeOwnerRequiredException):
        await access.require_owner(tree_id=tree.safe_id, user_id=member_user_id)


@pytest.mark.asyncio
async def test_require_access_allows_view_for_default_member(uow):
    tree = await create_family_tree_with_owner(uow)
    member_tree = await create_family_tree_with_owner(uow)
    member_user_id = member_tree.owner_user_id
    await add_tree_member(
        uow,
        tree_id=tree.safe_id,
        user_id=member_user_id,
        role=TreeMemberRole.MEMBER,
        permissions=[TreeAccessPermissions.VIEW],
    )
    access = TreeAccessService(uow)
    membership = await access.require_access(
        tree_id=tree.safe_id,
        user_id=member_user_id,
        permission=TreeAccessPermissions.VIEW,
    )
    assert membership.has_access(TreeAccessPermissions.VIEW)


@pytest.mark.asyncio
async def test_require_access_denies_edit_without_grant(uow):
    tree = await create_family_tree_with_owner(uow)
    member_tree = await create_family_tree_with_owner(uow)
    member_user_id = member_tree.owner_user_id
    await add_tree_member(
        uow,
        tree_id=tree.safe_id,
        user_id=member_user_id,
        role=TreeMemberRole.MEMBER,
        permissions=[TreeAccessPermissions.VIEW],
    )
    access = TreeAccessService(uow)
    with pytest.raises(TreeAccessDeniedException):
        await access.require_access(
            tree_id=tree.safe_id,
            user_id=member_user_id,
            permission=TreeAccessPermissions.PERSON_UPDATE,
        )


@pytest.mark.asyncio
async def test_edit_access_implies_view(uow):
    tree = await create_family_tree_with_owner(uow)
    member_tree = await create_family_tree_with_owner(uow)
    member_user_id = member_tree.owner_user_id
    await add_tree_member(
        uow,
        tree_id=tree.safe_id,
        user_id=member_user_id,
        role=TreeMemberRole.MEMBER,
        permissions=[TreeAccessPermissions.PERSON_UPDATE],
    )
    access = TreeAccessService(uow)
    membership = await access.require_access(
        tree_id=tree.safe_id,
        user_id=member_user_id,
        permission=TreeAccessPermissions.VIEW,
    )
    assert set(membership.effective_permissions()) == {
        TreeAccessPermissions.VIEW,
        TreeAccessPermissions.PERSON_UPDATE,
        TreeAccessPermissions.VIEW_BIRTH_DATE,
        TreeAccessPermissions.VIEW_PHOTO,
    }
