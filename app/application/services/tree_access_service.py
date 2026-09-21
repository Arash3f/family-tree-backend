from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.family_tree import TreeMembership
from app.domain.exceptions.family_tree_exceptions import (
    TreeAccessDeniedException,
    TreeMembershipDeniedException,
    TreeOwnerRequiredException,
)
from app.domain.shared.tree_access import TreeAccessPermissions


class TreeAccessService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def require_member(self, *, tree_id: UUID, user_id: UUID) -> TreeMembership:
        await self.uow.family_trees.get_or_raise(tree_id)
        membership = await self.uow.tree_memberships.get(
            tree_id=tree_id, user_id=user_id
        )
        if not membership:
            raise TreeMembershipDeniedException(
                detail=[f"tree_id={tree_id} user_id={user_id}"]
            )
        return membership

    async def require_owner(self, *, tree_id: UUID, user_id: UUID) -> TreeMembership:
        membership = await self.require_member(tree_id=tree_id, user_id=user_id)
        if not membership.is_owner():
            raise TreeOwnerRequiredException(
                detail=[f"tree_id={tree_id} user_id={user_id}"]
            )
        return membership

    async def require_access(
        self, *, tree_id: UUID, user_id: UUID, permission: str
    ) -> TreeMembership:
        membership = await self.require_member(tree_id=tree_id, user_id=user_id)
        if not membership.has_access(permission):
            raise TreeAccessDeniedException(
                detail=[f"tree_id={tree_id} user_id={user_id} permission={permission}"]
            )
        return membership

    async def require_tree_management(
        self, *, tree_id: UUID, user_id: UUID
    ) -> TreeMembership:
        """Owner or any member with a non-view write capability."""
        membership = await self.require_member(tree_id=tree_id, user_id=user_id)
        if not TreeAccessPermissions.grants_management(
            membership.effective_permissions()
        ):
            raise TreeAccessDeniedException(
                detail=[
                    f"tree_id={tree_id} user_id={user_id} permission=tree_management"
                ]
            )
        return membership
