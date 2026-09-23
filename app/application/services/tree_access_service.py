from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.entities.family_tree import TreeMemberRole, TreeMembership
from app.domain.exceptions.family_tree_exceptions import (
    TreeAccessDeniedException,
    TreeMembershipDeniedException,
    TreeOwnerRequiredException,
)
from app.domain.shared.tree_access import TreeAccessPermissions

#: Stand-in owner of the synthetic demo membership. The demo visitor is not a
#: user and never becomes one; a fixed nil id keeps the membership printable in
#: logs without implying an account exists behind it.
DEMO_VIEWER_ID = UUID(int=0)


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

    def is_demo_tree(self, tree_id: UUID) -> bool:
        """Whether this tree is the one published as the public demo."""
        demo_tree_id = settings.demo_tree_id
        return demo_tree_id is not None and tree_id == demo_tree_id

    def allows_anonymous(self, *, tree_id: UUID, permission: str) -> bool:
        """Whether this capability on this tree is readable without signing in.

        @param tree_id - The tree being reached for.
        @param permission - The capability the route demands.

        @returns True only for the configured demo tree and a demo capability.
        """
        return self.is_demo_tree(tree_id) and TreeAccessPermissions.grants_demo(
            permission
        )

    async def require_demo_access(
        self, *, tree_id: UUID, permission: str
    ) -> TreeMembership:
        """Grant a signed-out visitor read access to the demo tree.

        This is the only path in the service that answers without a user, and it
        is deliberately narrow: one configured tree, and only the capabilities in
        `TreeAccessPermissions.DEMO`. Every write capability is outside that set,
        so a demo visitor is refused by the same check that refuses anyone else.

        @param tree_id - The tree being reached for.
        @param permission - The capability the route demands.

        @returns A synthetic read-only membership, not persisted anywhere.

        @throws {AppException} TreeMembershipDeniedException - When the demo is
            off, the tree is not the demo tree, or the capability is not one the
            demo grants.
        """
        if not self.allows_anonymous(tree_id=tree_id, permission=permission):
            raise TreeMembershipDeniedException(
                detail=[f"tree_id={tree_id} user=anonymous permission={permission}"]
            )

        # Still proves the tree exists, so a stale DEMO_TREE_ID reads as a
        # missing tree rather than an empty one.
        await self.uow.family_trees.get_or_raise(tree_id)
        return TreeMembership(
            id=None,
            tree_id=tree_id,
            user_id=DEMO_VIEWER_ID,
            role=TreeMemberRole.MEMBER,
            permissions=list(TreeAccessPermissions.DEMO),
        )

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
