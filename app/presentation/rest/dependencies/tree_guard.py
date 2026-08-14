from uuid import UUID

from fastapi import Depends

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.family_tree import TreeMembership
from app.domain.entities.user import User
from app.domain.shared.tree_access import TreeAccessPermissions
from app.presentation.rest.dependencies.auth_dependencies import get_current_user
from app.presentation.rest.utils.dependencies import get_uow


async def require_tree_member(
    tree_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> TreeMembership:
    async with uow:
        return await TreeAccessService(uow).require_member(
            tree_id=tree_id, user_id=current_user.safe_id
        )


class RequireTreeAccess:
    """Require membership plus a specific per-tree capability."""

    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(
        self,
        tree_id: UUID,
        current_user: User = Depends(get_current_user),
        uow: UnitOfWork = Depends(get_uow),
    ) -> TreeMembership:
        async with uow:
            return await TreeAccessService(uow).require_access(
                tree_id=tree_id,
                user_id=current_user.safe_id,
                permission=self.permission,
            )


require_tree_view = RequireTreeAccess(TreeAccessPermissions.VIEW)
require_tree_edit = RequireTreeAccess(TreeAccessPermissions.EDIT)
require_tree_add_persons = RequireTreeAccess(TreeAccessPermissions.ADD_PERSONS)
