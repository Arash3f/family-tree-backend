from uuid import UUID

from app.application.dto.family_tree.family_tree_dto import (
    FamilyTreeMapper,
    FamilyTreeResponseDTO,
    FamilyTreeUpdateDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_access_service import TreeAccessService


class UpdateFamilyTreeUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(
        self, *, tree_id: UUID, user_id: UUID, dto: FamilyTreeUpdateDTO
    ) -> FamilyTreeResponseDTO:
        async with self.uow:
            await self.access.require_owner(tree_id=tree_id, user_id=user_id)
            tree = await self.uow.family_trees.get_or_raise(tree_id)
            tree.name = dto.name
            tree = await self.uow.family_trees.update(tree)
            await self.uow.commit()
            return FamilyTreeMapper.to_response(tree)


class DeleteFamilyTreeUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(self, *, tree_id: UUID, user_id: UUID) -> None:
        async with self.uow:
            await self.access.require_owner(tree_id=tree_id, user_id=user_id)
            await self.uow.family_trees.delete(tree_id)
            await self.uow.commit()
