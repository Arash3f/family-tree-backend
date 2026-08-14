from uuid import UUID

from strawberry.types import Info

from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.user import User
from app.domain.shared.permissions import Permissions
from app.domain.shared.tree_access import TreeAccessPermissions
from app.presentation.graphql.auth import require_permission

# Map system RBAC permission used on genealogy ops → per-tree capability.
RBAC_TO_TREE_ACCESS: dict[str, str] = {
    Permissions.PERSON_READ: TreeAccessPermissions.VIEW,
    Permissions.PERSON_CREATE: TreeAccessPermissions.ADD_PERSONS,
    Permissions.PERSON_UPDATE: TreeAccessPermissions.EDIT,
    Permissions.PERSON_DELETE: TreeAccessPermissions.EDIT,
    Permissions.MARRIAGE_READ: TreeAccessPermissions.VIEW,
    Permissions.MARRIAGE_CREATE: TreeAccessPermissions.ADD_PERSONS,
    Permissions.MARRIAGE_UPDATE: TreeAccessPermissions.EDIT,
    Permissions.MARRIAGE_DELETE: TreeAccessPermissions.EDIT,
    Permissions.MARRIAGE_DIVORCE: TreeAccessPermissions.EDIT,
    Permissions.MEDIA_UPLOAD: TreeAccessPermissions.EDIT,
}


async def require_tree_member_with_access(
    info: Info, tree_id: UUID, permission: str
) -> User:
    user = await require_permission(info, permission)
    tree_access = RBAC_TO_TREE_ACCESS.get(permission, TreeAccessPermissions.VIEW)
    async with info.context.uow:
        await TreeAccessService(info.context.uow).require_access(
            tree_id=tree_id,
            user_id=user.safe_id,
            permission=tree_access,
        )
    return user
