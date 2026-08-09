from uuid import UUID

from app.application.dto.family_tree.family_tree_dto import (
    FamilyTreeMapper,
    TreeMemberAddDTO,
    TreeMembershipResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_access_service import TreeAccessService
from app.domain.entities.family_tree import TreeMemberRole, TreeMembership
from app.domain.exceptions.family_tree_exceptions import (
    CannotRemoveLastOwnerException,
    TreeMemberAlreadyExistsException,
)


class AddTreeMemberUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(
        self, *, tree_id: UUID, actor_user_id: UUID, dto: TreeMemberAddDTO
    ) -> TreeMembershipResponseDTO:
        async with self.uow:
            await self.access.require_owner(tree_id=tree_id, user_id=actor_user_id)
            await self.uow.users.get_or_raise(user_id=dto.user_id)

            existing = await self.uow.tree_memberships.get(
                tree_id=tree_id, user_id=dto.user_id
            )
            if existing:
                raise TreeMemberAlreadyExistsException(
                    detail=[f"tree_id={tree_id} user_id={dto.user_id}"]
                )

            membership = await self.uow.tree_memberships.create(
                TreeMembership(
                    id=None,
                    tree_id=tree_id,
                    user_id=dto.user_id,
                    role=TreeMemberRole.MEMBER,
                )
            )
            await self.uow.commit()
            return FamilyTreeMapper.membership_to_response(membership)


class RemoveTreeMemberUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(
        self, *, tree_id: UUID, actor_user_id: UUID, target_user_id: UUID
    ) -> None:
        async with self.uow:
            await self.access.require_owner(tree_id=tree_id, user_id=actor_user_id)
            membership = await self.uow.tree_memberships.get_or_raise(
                tree_id=tree_id, user_id=target_user_id
            )

            if membership.is_owner():
                owners = await self.uow.tree_memberships.count_owners(tree_id)
                if owners <= 1:
                    raise CannotRemoveLastOwnerException(
                        detail=[f"tree_id={tree_id}"]
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
            members = await self.uow.tree_memberships.list_by_tree(tree_id)
            return [FamilyTreeMapper.membership_to_response(m) for m in members]
