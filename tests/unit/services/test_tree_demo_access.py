"""One tree may be published as a public read-only demo.

These tests pin the boundary, which is the whole point of the feature: exactly
one configured tree, exactly the read capabilities, and nothing at all when
`DEMO_TREE_ID` is unset.
"""

from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.application.services.tree_access_service import (
    DEMO_VIEWER_ID,
    TreeAccessService,
)
from app.core.config import settings
from app.domain.entities.family_tree import FamilyTree
from app.domain.exceptions.family_tree_exceptions import TreeMembershipDeniedException
from app.domain.shared.tree_access import TreeAccessPermissions

DEMO_TREE_ID = UUID(int=101)
OTHER_TREE_ID = UUID(int=202)


@pytest.fixture
def demo_tree(monkeypatch, mock_uow):
    monkeypatch.setattr(settings, "DEMO_TREE_ID", str(DEMO_TREE_ID))
    mock_uow.family_trees.get_or_raise = AsyncMock(
        return_value=FamilyTree(
            id=DEMO_TREE_ID, name="Demo", owner_user_id=UUID(int=303)
        )
    )
    return TreeAccessService(mock_uow)


def test_demo_is_off_by_default():
    assert settings.DEMO_TREE_ID == ""
    assert settings.demo_tree_id is None


def test_nothing_is_public_while_the_demo_is_off(mock_uow):
    service = TreeAccessService(mock_uow)

    assert not service.is_demo_tree(DEMO_TREE_ID)
    assert not service.allows_anonymous(
        tree_id=DEMO_TREE_ID, permission=TreeAccessPermissions.VIEW
    )


def test_only_the_configured_tree_is_public(demo_tree):
    assert demo_tree.allows_anonymous(
        tree_id=DEMO_TREE_ID, permission=TreeAccessPermissions.VIEW
    )
    assert not demo_tree.allows_anonymous(
        tree_id=OTHER_TREE_ID, permission=TreeAccessPermissions.VIEW
    )


@pytest.mark.parametrize("permission", TreeAccessPermissions.MANAGEMENT)
def test_no_write_capability_is_ever_public(demo_tree, permission):
    assert not demo_tree.allows_anonymous(tree_id=DEMO_TREE_ID, permission=permission)


@pytest.mark.asyncio
@pytest.mark.parametrize("permission", TreeAccessPermissions.DEMO)
async def test_demo_membership_grants_each_read_capability(demo_tree, permission):
    membership = await demo_tree.require_demo_access(
        tree_id=DEMO_TREE_ID, permission=permission
    )

    assert membership.user_id == DEMO_VIEWER_ID
    assert membership.has_access(permission)
    assert not membership.is_owner()


@pytest.mark.asyncio
async def test_demo_membership_carries_no_write_capability(demo_tree):
    membership = await demo_tree.require_demo_access(
        tree_id=DEMO_TREE_ID, permission=TreeAccessPermissions.VIEW
    )

    granted = set(membership.effective_permissions())
    assert granted.isdisjoint(TreeAccessPermissions.MANAGEMENT)


@pytest.mark.asyncio
async def test_a_write_capability_is_refused_on_the_demo_tree(demo_tree):
    with pytest.raises(TreeMembershipDeniedException):
        await demo_tree.require_demo_access(
            tree_id=DEMO_TREE_ID, permission=TreeAccessPermissions.PERSON_CREATE
        )


@pytest.mark.asyncio
async def test_another_tree_is_refused_even_for_a_read(demo_tree):
    with pytest.raises(TreeMembershipDeniedException):
        await demo_tree.require_demo_access(
            tree_id=OTHER_TREE_ID, permission=TreeAccessPermissions.VIEW
        )


@pytest.mark.asyncio
async def test_reads_are_refused_while_the_demo_is_off(mock_uow):
    service = TreeAccessService(mock_uow)

    with pytest.raises(TreeMembershipDeniedException):
        await service.require_demo_access(
            tree_id=DEMO_TREE_ID, permission=TreeAccessPermissions.VIEW
        )
