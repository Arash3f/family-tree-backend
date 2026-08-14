"""Merge ticket category and tree membership permission heads

Revision ID: 0014_merge_ticket_and_membership
Revises: 0013_ticket_category_tree, 0013_tree_membership_permissions
Create Date: 2026-08-13 21:20:00.000000

"""

from typing import Sequence, Union

revision: str = "0014_merge_ticket_and_membership"
down_revision: Union[str, Sequence[str], None] = (
    "0013_ticket_category_tree",
    "0013_tree_membership_permissions",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
