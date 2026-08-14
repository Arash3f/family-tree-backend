from uuid import UUID

from app.application.dto.family_tree.family_tree_dto import (
    FamilyTreeMapper,
    FamilyTreeResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_access_service import TreeAccessService


class ListFamilyTreesUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, *, user_id: UUID) -> list[FamilyTreeResponseDTO]:
        async with self.uow:
            trees = await self.uow.family_trees.list_for_user(user_id)
            responses: list[FamilyTreeResponseDTO] = []
            for tree in trees:
                membership = await self.uow.tree_memberships.get(
                    tree_id=tree.safe_id, user_id=user_id
                )
                responses.append(
                    FamilyTreeMapper.to_response(
                        tree,
                        my_permissions=(
                            membership.effective_permissions() if membership else []
                        ),
                    )
                )
            return responses


class GetFamilyTreeUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(self, *, tree_id: UUID, user_id: UUID) -> FamilyTreeResponseDTO:
        async with self.uow:
            membership = await self.access.require_member(
                tree_id=tree_id, user_id=user_id
            )
            tree = await self.uow.family_trees.get_or_raise(tree_id)
            return FamilyTreeMapper.to_response(
                tree, my_permissions=membership.effective_permissions()
            )
