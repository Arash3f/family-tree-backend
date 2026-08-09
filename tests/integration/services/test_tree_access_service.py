import pytest

from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.family_tree import TreeMemberRole
from app.domain.exceptions.family_tree_exceptions import (
    TreeMembershipDeniedException,
    TreeOwnerRequiredException,
)
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
