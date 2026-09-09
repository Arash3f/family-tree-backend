from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.shared.tree_access import TreeAccessPermissions


async def tree_ids_manageable_by_user(uow: UnitOfWork, user_id: UUID) -> set[UUID]:
    memberships = await uow.tree_memberships.list_by_user(user_id)
    return {
        membership.tree_id
        for membership in memberships
        if membership.has_access(TreeAccessPermissions.TICKET_MANAGE)
    }


async def user_can_manage_tree_ticket(
    uow: UnitOfWork, user_id: UUID, family_tree_id: UUID | None
) -> bool:
    if family_tree_id is None:
        return False
    membership = await uow.tree_memberships.get(tree_id=family_tree_id, user_id=user_id)
    if not membership:
        return False
    return membership.has_access(TreeAccessPermissions.TICKET_MANAGE)


async def user_can_manage_ticket(
    uow: UnitOfWork,
    user_id: UUID,
    family_tree_id: UUID | None,
    *,
    has_system_reply: bool,
) -> bool:
    """System ``ticket_reply`` covers only unlinked tickets; tree tickets need
    tree-level ``ticket_manage`` (owners always have it).
    """
    if family_tree_id is None:
        return has_system_reply
    return await user_can_manage_tree_ticket(uow, user_id, family_tree_id)


def viewer_can_manage_ticket(
    family_tree_id: UUID | None,
    *,
    has_system_reply: bool,
    manageable_tree_ids: set[UUID],
) -> bool:
    if family_tree_id is None:
        return has_system_reply
    return family_tree_id in manageable_tree_ids
