from uuid import UUID

from fastapi import Depends

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.family_tree import TreeMembership
from app.domain.entities.user import User
from app.domain.shared.tree_access import TreeAccessPermissions
from app.presentation.dependencies import get_request_uow
from app.presentation.rest.dependencies.auth_dependencies import get_current_user


async def require_tree_member(
    tree_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_request_uow),
) -> TreeMembership:
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
        uow: UnitOfWork = Depends(get_request_uow),
    ) -> TreeMembership:
        return await TreeAccessService(uow).require_access(
            tree_id=tree_id,
            user_id=current_user.safe_id,
            permission=self.permission,
        )


require_tree_view = RequireTreeAccess(TreeAccessPermissions.VIEW)
require_tree_person_create = RequireTreeAccess(TreeAccessPermissions.PERSON_CREATE)
require_tree_person_update = RequireTreeAccess(TreeAccessPermissions.PERSON_UPDATE)
require_tree_person_delete = RequireTreeAccess(TreeAccessPermissions.PERSON_DELETE)
require_tree_marriage_create = RequireTreeAccess(TreeAccessPermissions.MARRIAGE_CREATE)
require_tree_marriage_update = RequireTreeAccess(TreeAccessPermissions.MARRIAGE_UPDATE)
require_tree_marriage_delete = RequireTreeAccess(TreeAccessPermissions.MARRIAGE_DELETE)
require_tree_marriage_divorce = RequireTreeAccess(
    TreeAccessPermissions.MARRIAGE_DIVORCE
)
require_tree_upload_photo = RequireTreeAccess(TreeAccessPermissions.UPLOAD_PHOTO)
require_tree_member_add = RequireTreeAccess(TreeAccessPermissions.MEMBER_ADD)
require_tree_member_remove = RequireTreeAccess(TreeAccessPermissions.MEMBER_REMOVE)
require_tree_view_birth_date = RequireTreeAccess(TreeAccessPermissions.VIEW_BIRTH_DATE)
require_tree_view_marriage_date = RequireTreeAccess(
    TreeAccessPermissions.VIEW_MARRIAGE_DATE
)
require_tree_view_photo = RequireTreeAccess(TreeAccessPermissions.VIEW_PHOTO)
