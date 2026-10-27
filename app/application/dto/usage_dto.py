from datetime import date
from uuid import UUID

from pydantic import BaseModel


class FreeLimitsDTO(BaseModel):
    owned_trees: int
    persons_per_tree: int
    marriages_per_tree: int


class TreeUsageDTO(BaseModel):
    tree_id: UUID
    name: str
    persons: int
    marriages: int


class AccountUsageDTO(BaseModel):
    # The plan in force today, so a lapsed paid plan already reads "free".
    account_type: str
    paid_until: date | None = None
    # Days the paid plan still covers, today included; None when it never lapses.
    days_left: int | None = None
    # Whether the free quotas below apply to this account right now.
    limited: bool
    free_limits: FreeLimitsDTO
    owned_trees: int
    trees: list[TreeUsageDTO]
