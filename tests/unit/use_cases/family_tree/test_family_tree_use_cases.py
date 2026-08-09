from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.application.dto.family_tree.family_tree_dto import (
    FamilyTreeCreateDTO,
    FamilyTreeUpdateDTO,
    TreeMemberAddDTO,
)
from app.application.use_cases.family_tree.create_family_tree_use_case import (
    CreateFamilyTreeUseCase,
)
from app.application.use_cases.family_tree.get_family_tree_use_case import (
    GetFamilyTreeUseCase,
    ListFamilyTreesUseCase,
)
from app.application.use_cases.family_tree.tree_member_use_cases import (
    AddTreeMemberUseCase,
    ListTreeMembersUseCase,
    RemoveTreeMemberUseCase,
)
from app.application.use_cases.family_tree.update_family_tree_use_case import (
    DeleteFamilyTreeUseCase,
    UpdateFamilyTreeUseCase,
)
from app.domain.entities.family_tree import FamilyTree, TreeMemberRole, TreeMembership
from app.domain.exceptions.family_tree_exceptions import (
    CannotRemoveLastOwnerException,
    TreeMemberAlreadyExistsException,
    TreeMembershipDeniedException,
    TreeOwnerRequiredException,
)

TREE_ID = UUID(int=11)
OWNER_ID = UUID(int=22)
MEMBER_ID = UUID(int=33)
OUTSIDER_ID = UUID(int=44)


def _tree(name: str = "Ancestors") -> FamilyTree:
    return FamilyTree(id=TREE_ID, name=name, owner_user_id=OWNER_ID)


def _membership(user_id: UUID, role: TreeMemberRole) -> TreeMembership:
    return TreeMembership(id=uuid4(), tree_id=TREE_ID, user_id=user_id, role=role)


def _memberships(mock_uow, *, present: TreeMembership | None):
    mock_uow.family_trees.get_or_raise = AsyncMock(return_value=_tree())
    mock_uow.tree_memberships.get = AsyncMock(return_value=present)


# ============================================================
# CREATE
# ============================================================


@pytest.mark.asyncio
async def test_create_family_tree_registers_the_creator_as_owner(mock_uow):
    mock_uow.family_trees.create = AsyncMock(return_value=_tree())
    mock_uow.tree_memberships.create = AsyncMock()

    result = await CreateFamilyTreeUseCase(mock_uow).execute(
        FamilyTreeCreateDTO(name="Ancestors"), owner_user_id=OWNER_ID
    )

    assert result.id == TREE_ID
    membership = mock_uow.tree_memberships.create.await_args.args[0]
    assert membership.user_id == OWNER_ID
    assert membership.role is TreeMemberRole.OWNER
    mock_uow.commit.assert_awaited_once()


# ============================================================
# READ
# ============================================================


@pytest.mark.asyncio
async def test_list_family_trees_asks_only_for_the_users_trees(mock_uow):
    mock_uow.family_trees.list_for_user = AsyncMock(return_value=[_tree()])

    result = await ListFamilyTreesUseCase(mock_uow).execute(user_id=OWNER_ID)

    assert [t.id for t in result] == [TREE_ID]
    mock_uow.family_trees.list_for_user.assert_awaited_once_with(OWNER_ID)


@pytest.mark.asyncio
async def test_get_family_tree_allows_a_plain_member(mock_uow):
    _memberships(mock_uow, present=_membership(MEMBER_ID, TreeMemberRole.MEMBER))

    result = await GetFamilyTreeUseCase(mock_uow).execute(
        tree_id=TREE_ID, user_id=MEMBER_ID
    )

    assert result.id == TREE_ID


@pytest.mark.asyncio
async def test_get_family_tree_rejects_a_non_member(mock_uow):
    _memberships(mock_uow, present=None)

    with pytest.raises(TreeMembershipDeniedException):
        await GetFamilyTreeUseCase(mock_uow).execute(
            tree_id=TREE_ID, user_id=OUTSIDER_ID
        )


# ============================================================
# UPDATE / DELETE
# ============================================================


@pytest.mark.asyncio
async def test_update_family_tree_renames_it_for_the_owner(mock_uow):
    _memberships(mock_uow, present=_membership(OWNER_ID, TreeMemberRole.OWNER))
    mock_uow.family_trees.update = AsyncMock(side_effect=lambda tree: tree)

    result = await UpdateFamilyTreeUseCase(mock_uow).execute(
        tree_id=TREE_ID, user_id=OWNER_ID, dto=FamilyTreeUpdateDTO(name="Renamed")
    )

    assert result.name == "Renamed"
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_family_tree_rejects_a_plain_member(mock_uow):
    _memberships(mock_uow, present=_membership(MEMBER_ID, TreeMemberRole.MEMBER))
    mock_uow.family_trees.update = AsyncMock()

    with pytest.raises(TreeOwnerRequiredException):
        await UpdateFamilyTreeUseCase(mock_uow).execute(
            tree_id=TREE_ID, user_id=MEMBER_ID, dto=FamilyTreeUpdateDTO(name="Hijacked")
        )

    mock_uow.family_trees.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_family_tree_rejects_a_plain_member(mock_uow):
    _memberships(mock_uow, present=_membership(MEMBER_ID, TreeMemberRole.MEMBER))
    mock_uow.family_trees.delete = AsyncMock()

    with pytest.raises(TreeOwnerRequiredException):
        await DeleteFamilyTreeUseCase(mock_uow).execute(
            tree_id=TREE_ID, user_id=MEMBER_ID
        )

    mock_uow.family_trees.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_family_tree_succeeds_for_the_owner(mock_uow):
    _memberships(mock_uow, present=_membership(OWNER_ID, TreeMemberRole.OWNER))
    mock_uow.family_trees.delete = AsyncMock()

    await DeleteFamilyTreeUseCase(mock_uow).execute(tree_id=TREE_ID, user_id=OWNER_ID)

    mock_uow.family_trees.delete.assert_awaited_once_with(TREE_ID)


# ============================================================
# MEMBERSHIP
# ============================================================


@pytest.mark.asyncio
async def test_add_tree_member_joins_with_the_member_role(mock_uow):
    mock_uow.family_trees.get_or_raise = AsyncMock(return_value=_tree())
    mock_uow.tree_memberships.get = AsyncMock(
        side_effect=[_membership(OWNER_ID, TreeMemberRole.OWNER), None]
    )
    mock_uow.tree_memberships.create = AsyncMock(
        return_value=_membership(MEMBER_ID, TreeMemberRole.MEMBER)
    )

    result = await AddTreeMemberUseCase(mock_uow).execute(
        tree_id=TREE_ID,
        actor_user_id=OWNER_ID,
        dto=TreeMemberAddDTO(user_id=MEMBER_ID),
    )

    assert result.role is TreeMemberRole.MEMBER
    created = mock_uow.tree_memberships.create.await_args.args[0]
    assert created.role is TreeMemberRole.MEMBER


@pytest.mark.asyncio
async def test_add_tree_member_rejects_a_duplicate(mock_uow):
    mock_uow.family_trees.get_or_raise = AsyncMock(return_value=_tree())
    mock_uow.tree_memberships.get = AsyncMock(
        side_effect=[
            _membership(OWNER_ID, TreeMemberRole.OWNER),
            _membership(MEMBER_ID, TreeMemberRole.MEMBER),
        ]
    )
    mock_uow.tree_memberships.create = AsyncMock()

    with pytest.raises(TreeMemberAlreadyExistsException):
        await AddTreeMemberUseCase(mock_uow).execute(
            tree_id=TREE_ID,
            actor_user_id=OWNER_ID,
            dto=TreeMemberAddDTO(user_id=MEMBER_ID),
        )

    mock_uow.tree_memberships.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_tree_member_rejects_a_plain_member_as_actor(mock_uow):
    _memberships(mock_uow, present=_membership(MEMBER_ID, TreeMemberRole.MEMBER))
    mock_uow.tree_memberships.create = AsyncMock()

    with pytest.raises(TreeOwnerRequiredException):
        await AddTreeMemberUseCase(mock_uow).execute(
            tree_id=TREE_ID,
            actor_user_id=MEMBER_ID,
            dto=TreeMemberAddDTO(user_id=OUTSIDER_ID),
        )

    mock_uow.tree_memberships.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_tree_member_removes_a_plain_member(mock_uow):
    _memberships(mock_uow, present=_membership(OWNER_ID, TreeMemberRole.OWNER))
    mock_uow.tree_memberships.get_or_raise = AsyncMock(
        return_value=_membership(MEMBER_ID, TreeMemberRole.MEMBER)
    )
    mock_uow.tree_memberships.delete = AsyncMock()

    await RemoveTreeMemberUseCase(mock_uow).execute(
        tree_id=TREE_ID, actor_user_id=OWNER_ID, target_user_id=MEMBER_ID
    )

    mock_uow.tree_memberships.delete.assert_awaited_once_with(
        tree_id=TREE_ID, user_id=MEMBER_ID
    )


@pytest.mark.asyncio
async def test_remove_tree_member_keeps_the_last_owner(mock_uow):
    """A tree left without an owner could never be administered again."""
    _memberships(mock_uow, present=_membership(OWNER_ID, TreeMemberRole.OWNER))
    mock_uow.tree_memberships.get_or_raise = AsyncMock(
        return_value=_membership(OWNER_ID, TreeMemberRole.OWNER)
    )
    mock_uow.tree_memberships.count_owners = AsyncMock(return_value=1)
    mock_uow.tree_memberships.delete = AsyncMock()

    with pytest.raises(CannotRemoveLastOwnerException):
        await RemoveTreeMemberUseCase(mock_uow).execute(
            tree_id=TREE_ID, actor_user_id=OWNER_ID, target_user_id=OWNER_ID
        )

    mock_uow.tree_memberships.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_tree_member_allows_dropping_one_of_several_owners(mock_uow):
    _memberships(mock_uow, present=_membership(OWNER_ID, TreeMemberRole.OWNER))
    mock_uow.tree_memberships.get_or_raise = AsyncMock(
        return_value=_membership(MEMBER_ID, TreeMemberRole.OWNER)
    )
    mock_uow.tree_memberships.count_owners = AsyncMock(return_value=2)
    mock_uow.tree_memberships.delete = AsyncMock()

    await RemoveTreeMemberUseCase(mock_uow).execute(
        tree_id=TREE_ID, actor_user_id=OWNER_ID, target_user_id=MEMBER_ID
    )

    mock_uow.tree_memberships.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_tree_members_rejects_a_non_member(mock_uow):
    _memberships(mock_uow, present=None)
    mock_uow.tree_memberships.list_by_tree = AsyncMock()

    with pytest.raises(TreeMembershipDeniedException):
        await ListTreeMembersUseCase(mock_uow).execute(
            tree_id=TREE_ID, user_id=OUTSIDER_ID
        )

    mock_uow.tree_memberships.list_by_tree.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_tree_members_returns_the_roster_for_a_member(mock_uow):
    _memberships(mock_uow, present=_membership(MEMBER_ID, TreeMemberRole.MEMBER))
    mock_uow.tree_memberships.list_by_tree = AsyncMock(
        return_value=[
            _membership(OWNER_ID, TreeMemberRole.OWNER),
            _membership(MEMBER_ID, TreeMemberRole.MEMBER),
        ]
    )

    result = await ListTreeMembersUseCase(mock_uow).execute(
        tree_id=TREE_ID, user_id=MEMBER_ID
    )

    assert [m.role for m in result] == [TreeMemberRole.OWNER, TreeMemberRole.MEMBER]
