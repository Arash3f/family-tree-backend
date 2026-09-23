from uuid import UUID

from app.application.dto.family_tree.family_tree_dto import (
    FamilyTreeMapper,
    FamilyTreeResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_access_service import TreeAccessService
from app.core.config import settings
from app.domain.exceptions.family_tree_exceptions import (
    FamilyTreeNotFoundException,
)
from app.domain.shared.tree_access import TreeAccessPermissions


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


class GetDemoFamilyTreeUseCase:
    """Resolve the publicly published demo tree for a signed-out visitor.

    Kept separate from `GetFamilyTreeUseCase` rather than folded into it behind
    an optional user id: the two answer to different authorization rules, and a
    single method that silently drops the membership check when the caller is
    None is exactly the shape that later gets called by accident.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.access = TreeAccessService(uow)

    async def execute(self) -> FamilyTreeResponseDTO:
        """Return the demo tree with the read-only permissions it grants.

        @returns The tree, with `my_permissions` set to the demo capabilities so
            the client renders it read-only from the same field it always reads.

        @throws {AppException} FamilyTreeNotFoundException - When no demo tree is
            configured, or `DEMO_TREE_ID` names a tree that no longer exists.
        """
        tree_id = settings.demo_tree_id
        if tree_id is None:
            raise FamilyTreeNotFoundException(detail=["no demo tree is configured"])

        async with self.uow:
            membership = await self.access.require_demo_access(
                tree_id=tree_id, permission=TreeAccessPermissions.VIEW
            )
            tree = await self.uow.family_trees.get_or_raise(tree_id)
            return FamilyTreeMapper.to_response(
                tree, my_permissions=membership.effective_permissions()
            )
