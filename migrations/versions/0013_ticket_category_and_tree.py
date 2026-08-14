"""Add ticket category and optional family_tree_id

Revision ID: 0013_ticket_category_tree
Revises: 0012_permission_descriptions, 0012_user_fullname
Create Date: 2026-08-13 20:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_ticket_category_tree"
down_revision: Union[str, Sequence[str], None] = (
    "0012_permission_descriptions",
    "0012_user_fullname",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CATEGORIES = (
    "general",
    "account",
    "technical",
    "bug",
    "feature_request",
    "other",
)


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column(
            "category",
            sa.String(length=32),
            nullable=False,
            server_default="general",
        ),
    )
    op.create_index("ix_tickets_category", "tickets", ["category"], unique=False)
    op.create_check_constraint(
        "ck_ticket_category",
        "tickets",
        "category IN (" + ", ".join(f"'{c}'" for c in _CATEGORIES) + ")",
    )

    op.add_column(
        "tickets",
        sa.Column("family_tree_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_tickets_family_tree_id",
        "tickets",
        ["family_tree_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_tickets_family_tree_id",
        "tickets",
        "family_trees",
        ["family_tree_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.alter_column("tickets", "category", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_tickets_family_tree_id", "tickets", type_="foreignkey")
    op.drop_index("ix_tickets_family_tree_id", table_name="tickets")
    op.drop_column("tickets", "family_tree_id")
    op.drop_constraint("ck_ticket_category", "tickets", type_="check")
    op.drop_index("ix_tickets_category", table_name="tickets")
    op.drop_column("tickets", "category")
