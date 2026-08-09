from uuid import UUID

from fastapi import Depends

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.family_tree import TreeMembership
from app.domain.entities.user import User
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
