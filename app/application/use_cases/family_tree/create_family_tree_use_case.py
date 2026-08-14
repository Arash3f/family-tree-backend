from uuid import UUID

from app.application.dto.family_tree.family_tree_dto import (
    FamilyTreeCreateDTO,
    FamilyTreeMapper,
    FamilyTreeResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.family_tree import FamilyTree, TreeMemberRole, TreeMembership
from app.domain.shared.tree_access import TreeAccessPermissions


class CreateFamilyTreeUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self, dto: FamilyTreeCreateDTO, *, owner_user_id: UUID
    ) -> FamilyTreeResponseDTO:
        async with self.uow:
            await self.uow.users.get_or_raise(user_id=owner_user_id)

            tree = await self.uow.family_trees.create(
                FamilyTree(
                    id=None,
                    name=dto.name,
                    owner_user_id=owner_user_id,
                )
            )
            await self.uow.tree_memberships.create(
                TreeMembership(
                    id=None,
                    tree_id=tree.safe_id,
                    user_id=owner_user_id,
                    role=TreeMemberRole.OWNER,
                    permissions=list(TreeAccessPermissions.ALL),
                )
            )
            await self.uow.commit()
            return FamilyTreeMapper.to_response(
                tree, my_permissions=sorted(TreeAccessPermissions.ALL)
            )
