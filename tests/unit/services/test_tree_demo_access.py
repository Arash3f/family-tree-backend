"""Demo trees may be published as public read-only demos.

These tests pin the boundary, which is the whole point of the feature: only the
configured tree id(s), exactly the read capabilities, and nothing at all when
every `DEMO_TREE_ID*` is unset. Locale-specific slots (`_FA` / `_EN`) and the
legacy `DEMO_TREE_ID` fallback are all treated as public.
"""

from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.application.services.tree_access_service import (
    DEMO_VIEWER_ID,
    TreeAccessService,
)
from app.core.config import AppSettings, settings
from app.domain.entities.family_tree import FamilyTree
from app.domain.exceptions.family_tree_exceptions import TreeMembershipDeniedException
from app.domain.shared.tree_access import TreeAccessPermissions

DEMO_TREE_ID = UUID(int=101)
DEMO_TREE_ID_FA = UUID(int=111)
DEMO_TREE_ID_EN = UUID(int=112)
OTHER_TREE_ID = UUID(int=202)


@pytest.fixture
def demo_tree(monkeypatch, mock_uow):
    monkeypatch.setattr(settings, "DEMO_TREE_ID", str(DEMO_TREE_ID))
    monkeypatch.setattr(settings, "DEMO_TREE_ID_FA", "")
    monkeypatch.setattr(settings, "DEMO_TREE_ID_EN", "")
    mock_uow.family_trees.get_or_raise = AsyncMock(
        return_value=FamilyTree(
            id=DEMO_TREE_ID, name="Demo", owner_user_id=UUID(int=303)
        )
    )
    return TreeAccessService(mock_uow)


@pytest.fixture
def locale_demo_trees(monkeypatch, mock_uow):
    monkeypatch.setattr(settings, "DEMO_TREE_ID", "")
    monkeypatch.setattr(settings, "DEMO_TREE_ID_FA", str(DEMO_TREE_ID_FA))
    monkeypatch.setattr(settings, "DEMO_TREE_ID_EN", str(DEMO_TREE_ID_EN))
    mock_uow.family_trees.get_or_raise = AsyncMock(
        side_effect=lambda tree_id: FamilyTree(
            id=tree_id, name="Demo", owner_user_id=UUID(int=303)
        )
    )
    return TreeAccessService(mock_uow)


def test_demo_defaults_are_empty():
    assert AppSettings.model_fields["DEMO_TREE_ID"].default == ""
    assert AppSettings.model_fields["DEMO_TREE_ID_FA"].default == ""
    assert AppSettings.model_fields["DEMO_TREE_ID_EN"].default == ""


def test_nothing_is_public_while_the_demo_is_off(mock_uow, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_TREE_ID", "")
    monkeypatch.setattr(settings, "DEMO_TREE_ID_FA", "")
    monkeypatch.setattr(settings, "DEMO_TREE_ID_EN", "")
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


def test_both_locale_trees_are_public(locale_demo_trees):
    assert locale_demo_trees.is_demo_tree(DEMO_TREE_ID_FA)
    assert locale_demo_trees.is_demo_tree(DEMO_TREE_ID_EN)
    assert not locale_demo_trees.is_demo_tree(OTHER_TREE_ID)


def test_locale_resolution_prefers_specific_ids(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_TREE_ID", str(DEMO_TREE_ID))
    monkeypatch.setattr(settings, "DEMO_TREE_ID_FA", str(DEMO_TREE_ID_FA))
    monkeypatch.setattr(settings, "DEMO_TREE_ID_EN", str(DEMO_TREE_ID_EN))

    assert settings.demo_tree_id_for_locale("fa") == DEMO_TREE_ID_FA
    assert settings.demo_tree_id_for_locale("en") == DEMO_TREE_ID_EN


def test_locale_resolution_falls_back_to_legacy_id(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_TREE_ID", str(DEMO_TREE_ID))
    monkeypatch.setattr(settings, "DEMO_TREE_ID_FA", "")
    monkeypatch.setattr(settings, "DEMO_TREE_ID_EN", "")

    assert settings.demo_tree_id_for_locale("fa") == DEMO_TREE_ID
    assert settings.demo_tree_id_for_locale("en") == DEMO_TREE_ID


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
async def test_reads_are_refused_while_the_demo_is_off(mock_uow, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_TREE_ID", "")
    monkeypatch.setattr(settings, "DEMO_TREE_ID_FA", "")
    monkeypatch.setattr(settings, "DEMO_TREE_ID_EN", "")
    service = TreeAccessService(mock_uow)

    with pytest.raises(TreeMembershipDeniedException):
        await service.require_demo_access(
            tree_id=DEMO_TREE_ID, permission=TreeAccessPermissions.VIEW
        )
