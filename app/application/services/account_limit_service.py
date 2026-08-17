from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.family_tree_exceptions import FreeAccountLimitException
from app.domain.shared.account_type import (
    FREE_MAX_MARRIAGES_PER_TREE,
    FREE_MAX_OWNED_TREES,
    FREE_MAX_PERSONS_PER_TREE,
)
from app.infrastructure.database.models.family_tree_model import FamilyTreeModel
from app.infrastructure.database.models.marriage_model import MarriageModel
from app.infrastructure.database.models.person_model import PersonModel
from app.infrastructure.database.models.user_model import UserModel


class AccountLimitService:
    """Enforce free-account quotas against the tree owner's plan."""

    async def assert_can_create_tree(
        self, uow: UnitOfWork, *, owner_user_id: UUID
    ) -> None:
        owner = await uow.users.get_for_update(owner_user_id)
        if owner is None or not owner.is_free:
            return

        owned = await uow.family_trees.count_owned_by_user(owner_user_id)
        if owned >= FREE_MAX_OWNED_TREES:
            raise FreeAccountLimitException(
                detail=[f"free accounts may own at most {FREE_MAX_OWNED_TREES} tree(s)"]
            )

    async def assert_can_create_persons(
        self,
        uow: UnitOfWork,
        *,
        tree_id: UUID,
        additional: int = 1,
    ) -> None:
        if additional <= 0:
            return
        owner = await self._lock_tree_owner(uow, tree_id)
        if owner is None or not owner.is_free:
            return
        current = await self._count_persons_locked(uow.session, tree_id)
        if current + additional > FREE_MAX_PERSONS_PER_TREE:
            raise FreeAccountLimitException(
                detail=[
                    f"free accounts may have at most {FREE_MAX_PERSONS_PER_TREE} "
                    "person(s) per tree"
                ]
            )

    async def assert_can_create_marriages(
        self,
        uow: UnitOfWork,
        *,
        tree_id: UUID,
        additional: int = 1,
    ) -> None:
        if additional <= 0:
            return
        owner = await self._lock_tree_owner(uow, tree_id)
        if owner is None or not owner.is_free:
            return
        current = await self._count_marriages_locked(uow.session, tree_id)
        if current + additional > FREE_MAX_MARRIAGES_PER_TREE:
            raise FreeAccountLimitException(
                detail=[
                    f"free accounts may have at most {FREE_MAX_MARRIAGES_PER_TREE} "
                    "marriage(s) per tree"
                ]
            )

    async def _lock_tree_owner(self, uow: UnitOfWork, tree_id: UUID):
        tree = await uow.family_trees.get_or_raise(tree_id)
        return await uow.users.get_for_update(tree.owner_user_id)

    @staticmethod
    async def _count_persons_locked(session: AsyncSession, tree_id: UUID) -> int:
        stmt = select(func.count(PersonModel.id)).where(
            PersonModel.tree_id == tree_id
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def _count_marriages_locked(session: AsyncSession, tree_id: UUID) -> int:
        stmt = select(func.count(MarriageModel.id)).where(
            MarriageModel.tree_id == tree_id
        )
        result = await session.execute(stmt)
        return result.scalar() or 0
