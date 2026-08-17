from uuid import UUID

from app.application.dto.family_tree.family_tree_dto import (
    FamilyTreeMapper,
    TreeMemberAddDTO,
    TreeMemberUpdateDTO,
    TreeMembershipResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.family_tree import TreeMemberRole, TreeMembership
from app.domain.exceptions.family_tree_exceptions import (
    TreeAccessDeniedException,
    TreeMemberAlreadyExistsException,
)
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.domain.shared.tree_access import TreeAccessPermissions


def _ensure_delegable_permissions(
    actor: TreeMembership, requested: list[str], *, tree_id: UUID
) -> None:
    """Prevent a non-owner from granting capabilities they do not hold."""
    missing = set(requested) - set(actor.effective_permissions())
    if missing:
        raise TreeAccessDeniedException(
            detail=[f"tree_id={tree_id} cannot delegate permissions={sorted(missing)}"]
        )


class AddTreeMemberUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(
        self, *, tree_id: UUID, actor_user_id: UUID, dto: TreeMemberAddDTO
    ) -> TreeMembershipResponseDTO:
        async with self.uow:
            actor = await self.access.require_access(
                tree_id=tree_id,
                user_id=actor_user_id,
                permission=TreeAccessPermissions.MEMBER_ADD,
            )
            _ensure_delegable_permissions(actor, dto.permissions, tree_id=tree_id)
            username = dto.username.strip()
            user = await self.uow.users.get_by_username(username)
            if user is None:
                raise UserNotFoundException(detail=[f"username={username}"])

            existing = await self.uow.tree_memberships.get(
                tree_id=tree_id, user_id=user.safe_id
            )
            if existing:
                raise TreeMemberAlreadyExistsException(
                    detail=[f"tree_id={tree_id} user_id={user.safe_id}"]
                )

            membership = await self.uow.tree_memberships.create(
                TreeMembership(
                    id=None,
                    tree_id=tree_id,
                    user_id=user.safe_id,
                    role=TreeMemberRole.MEMBER,
                    permissions=dto.permissions,
                )
            )
            await self.uow.commit()
            return FamilyTreeMapper.membership_to_response(
                membership, username=user.username
            )


class UpdateTreeMemberUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(
        self,
        *,
        tree_id: UUID,
        actor_user_id: UUID,
        target_user_id: UUID,
        dto: TreeMemberUpdateDTO,
    ) -> TreeMembershipResponseDTO:
        async with self.uow:
            actor = await self.access.require_access(
                tree_id=tree_id,
                user_id=actor_user_id,
                permission=TreeAccessPermissions.MEMBER_ADD,
            )
            if target_user_id == actor_user_id:
                raise TreeAccessDeniedException(
                    detail=[f"tree_id={tree_id} members cannot update themselves"]
                )
            _ensure_delegable_permissions(actor, dto.permissions, tree_id=tree_id)
            membership = await self.uow.tree_memberships.get_or_raise(
                tree_id=tree_id, user_id=target_user_id
            )
            if membership.is_owner():
                raise TreeAccessDeniedException(
                    detail=[f"tree_id={tree_id} owner permissions are immutable"]
                )

            membership.permissions = dto.permissions
            updated = await self.uow.tree_memberships.update(membership)
            await self.uow.commit()
            user = await self.uow.users.get(updated.user_id)
            return FamilyTreeMapper.membership_to_response(
                updated, username=user.username if user else None
            )


class RemoveTreeMemberUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(
        self, *, tree_id: UUID, actor_user_id: UUID, target_user_id: UUID
    ) -> None:
        async with self.uow:
            await self.access.require_access(
                tree_id=tree_id,
                user_id=actor_user_id,
                permission=TreeAccessPermissions.MEMBER_REMOVE,
            )
            membership = await self.uow.tree_memberships.get_or_raise(
                tree_id=tree_id, user_id=target_user_id
            )

            if membership.is_owner():
                raise TreeAccessDeniedException(
                    detail=[f"tree_id={tree_id} owners cannot be removed"]
                )

            await self.uow.tree_memberships.delete(
                tree_id=tree_id, user_id=target_user_id
            )
            await self.uow.commit()


class ListTreeMembersUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(
        self, *, tree_id: UUID, user_id: UUID
    ) -> list[TreeMembershipResponseDTO]:
        async with self.uow:
            await self.access.require_member(tree_id=tree_id, user_id=user_id)
            members_with_usernames = await self.uow.tree_memberships.list_by_tree_with_usernames(tree_id)
            return [
                FamilyTreeMapper.membership_to_response(membership, username=username)
                for membership, username in members_with_usernames
            ]
