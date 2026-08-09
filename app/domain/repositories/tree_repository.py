from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.family_tree import FamilyTree, TreeMembership
from app.domain.exceptions.family_tree_exceptions import (
    FamilyTreeNotFoundException,
    TreeMemberNotFoundException,
)


class TreeRepository(ABC):
    @abstractmethod
    async def create(self, tree: FamilyTree) -> FamilyTree: ...

    @abstractmethod
    async def get(self, tree_id: UUID) -> FamilyTree | None: ...

    @abstractmethod
    async def list_for_user(self, user_id: UUID) -> list[FamilyTree]: ...

    @abstractmethod
    async def update(self, tree: FamilyTree) -> FamilyTree: ...

    @abstractmethod
    async def delete(self, tree_id: UUID) -> None: ...

    async def get_or_raise(self, tree_id: UUID) -> FamilyTree:
        tree = await self.get(tree_id)
        if not tree:
            raise FamilyTreeNotFoundException(detail=[f"tree id is {tree_id}"])
        return tree


class TreeMembershipRepository(ABC):
    @abstractmethod
    async def create(self, membership: TreeMembership) -> TreeMembership: ...

    @abstractmethod
    async def get(
        self, tree_id: UUID, user_id: UUID
    ) -> TreeMembership | None: ...

    @abstractmethod
    async def list_by_tree(self, tree_id: UUID) -> list[TreeMembership]: ...

    @abstractmethod
    async def count_owners(self, tree_id: UUID) -> int: ...

    @abstractmethod
    async def delete(self, tree_id: UUID, user_id: UUID) -> None: ...

    async def get_or_raise(self, tree_id: UUID, user_id: UUID) -> TreeMembership:
        membership = await self.get(tree_id=tree_id, user_id=user_id)
        if not membership:
            raise TreeMemberNotFoundException(
                detail=[f"tree_id={tree_id} user_id={user_id}"]
            )
        return membership
