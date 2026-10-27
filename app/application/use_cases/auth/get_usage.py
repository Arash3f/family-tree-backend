from datetime import UTC, datetime
from uuid import UUID

from app.application.dto.usage_dto import AccountUsageDTO, FreeLimitsDTO, TreeUsageDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.shared.account_type import AccountType


class GetMyUsageUseCase:
    """What the caller's own trees hold, against the quotas of their plan."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: UUID) -> AccountUsageDTO:
        async with self.uow:
            user = await self.uow.users.get_or_raise(user_id)
            owned = await self.uow.family_trees.list_owned_by_user(user_id)
            trees = [
                TreeUsageDTO(
                    tree_id=tree.safe_id,
                    name=tree.name,
                    persons=await self.uow.persons.count_in_tree(tree.safe_id),
                    marriages=await self.uow.marriages.count_in_tree(tree.safe_id),
                )
                for tree in owned
            ]

        plan = user.effective_account_type
        days_left = None
        if plan is AccountType.PAID and user.paid_until is not None:
            days_left = (user.paid_until - datetime.now(UTC).date()).days + 1

        return AccountUsageDTO(
            account_type=plan.value,
            paid_until=user.paid_until,
            days_left=days_left,
            limited=user.is_free,
            free_limits=FreeLimitsDTO(
                owned_trees=settings.FREE_MAX_OWNED_TREES,
                persons_per_tree=settings.FREE_MAX_PERSONS_PER_TREE,
                marriages_per_tree=settings.FREE_MAX_MARRIAGES_PER_TREE,
            ),
            owned_trees=len(trees),
            trees=trees,
        )
