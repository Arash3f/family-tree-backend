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
