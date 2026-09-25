from uuid import UUID

from fastapi import Depends, Request

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.family_tree import TreeMembership
from app.domain.entities.user import User
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException
from app.domain.exceptions.family_tree_exceptions import TreeMembershipDeniedException
from app.domain.shared.tree_access import TreeAccessPermissions
from app.presentation.dependencies import get_request_uow
from app.presentation.rest.dependencies.auth_dependencies import (
    get_current_user,
    get_optional_current_user,
)
from app.presentation.rest.dependencies.rate_limit import rate_limit_demo


async def require_tree_member(
    tree_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_request_uow),
) -> TreeMembership:
    return await TreeAccessService(uow).require_member(
        tree_id=tree_id, user_id=current_user.safe_id
    )


class RequireTreeAccess:
    """Require membership plus a specific per-tree capability.

    One tree may also be published as a public read-only demo. Rather than giving
    that tree its own copy of every read route, the fallback lives here: a caller
    who is not a member is offered the demo membership, which carries only
    `TreeAccessPermissions.DEMO`. Every write guard asks for a capability outside
    that set, so nothing becomes writable by adding this, and with no
    `DEMO_TREE_ID*` set the fallback can never match at all.

    A caller with no credentials and no public read to fall back on still gets
    the same 401 as before — the demo must never turn an authentication failure
    into an authorization one.
    """

    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(
        self,
        tree_id: UUID,
        request: Request,
        current_user: User | None = Depends(get_optional_current_user),
        uow: UnitOfWork = Depends(get_request_uow),
    ) -> TreeMembership:
        service = TreeAccessService(uow)
        public = service.allows_anonymous(tree_id=tree_id, permission=self.permission)

        async def as_demo_visitor() -> TreeMembership:
            # Metered per IP, and only here: a member reading their own tree
            # never passes through this branch.
            await rate_limit_demo(request)
            return await service.require_demo_access(
                tree_id=tree_id, permission=self.permission
            )

        if current_user is None:
            if not public:
                raise InvalidCredentialsException()
            return await as_demo_visitor()

        try:
            return await service.require_access(
                tree_id=tree_id,
                user_id=current_user.safe_id,
                permission=self.permission,
            )
        except TreeMembershipDeniedException:
            # Not a member. A member who merely lacks the capability raises
            # TreeAccessDenied instead and is never handed the demo in its place.
            if not public:
                raise

        return await as_demo_visitor()


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
