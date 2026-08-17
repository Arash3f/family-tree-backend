from uuid import UUID

from strawberry.types import Info

from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.family_tree import TreeMembership
from app.domain.entities.user import User
from app.presentation.graphql.auth import get_current_user


async def require_tree_member_with_access(
    info: Info, tree_id: UUID, permission: str
) -> User:
    user, _ = await require_tree_membership_with_access(info, tree_id, permission)
    return user


async def require_tree_membership_with_access(
    info: Info, tree_id: UUID, tree_access: str
) -> tuple[User, TreeMembership]:
    user = await get_current_user(info)
    async with info.context.uow:
        membership = await TreeAccessService(info.context.uow).require_access(
            tree_id=tree_id,
            user_id=user.safe_id,
            permission=tree_access,
        )
    return user, membership
