"""Soft-delete for marriages, tickets, and tree_memberships.

Adds a `deleted_at` column to each table, mirroring the persons soft-delete
pattern (see 0008_genealogy_remaining_items.py). The natural-key unique
constraints on `marriages` and `tree_memberships` are converted to partial
unique indexes scoped to `deleted_at IS NULL`, so a soft-deleted row no
longer blocks recreating the same couple/date or the same tree/user pair.

Revision ID: 0019_soft_delete_mtt
Revises: 0018_user_account_type
Create Date: 2026-08-18 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019_soft_delete_mtt"
down_revision: Union[str, Sequence[str], None] = "0018_user_account_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- marriages ---
    op.add_column(
        "marriages",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_marriages_deleted_at",
        "marriages",
        ["deleted_at"],
        unique=False,
    )
    op.drop_constraint(
        "uq_marriage_tree_couple_date", "marriages", type_="unique"
    )
    op.create_index(
        "uq_marriage_tree_couple_date",
        "marriages",
        ["tree_id", "spouse_a_id", "spouse_b_id", "married_at"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # --- tickets ---
    op.add_column(
        "tickets",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_tickets_deleted_at",
        "tickets",
        ["deleted_at"],
        unique=False,
    )

    # --- tree_memberships ---
    op.add_column(
        "tree_memberships",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_tree_memberships_deleted_at",
        "tree_memberships",
        ["deleted_at"],
        unique=False,
    )
    op.drop_constraint(
        "uq_tree_membership_tree_user", "tree_memberships", type_="unique"
    )
    op.create_index(
        "uq_tree_membership_tree_user",
        "tree_memberships",
        ["tree_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    # Rebuilt without the soft-delete predicate first: dropping deleted_at
    # while the index still references it would take the uniqueness rule
    # down with the column and leave the table without one.

    # --- tree_memberships ---
    op.drop_index("uq_tree_membership_tree_user", table_name="tree_memberships")
    op.create_unique_constraint(
        "uq_tree_membership_tree_user",
        "tree_memberships",
        ["tree_id", "user_id"],
    )
    op.drop_index("ix_tree_memberships_deleted_at", table_name="tree_memberships")
    op.drop_column("tree_memberships", "deleted_at")

    # --- tickets ---
    op.drop_index("ix_tickets_deleted_at", table_name="tickets")
    op.drop_column("tickets", "deleted_at")

    # --- marriages ---
    op.drop_index("uq_marriage_tree_couple_date", table_name="marriages")
    op.create_unique_constraint(
        "uq_marriage_tree_couple_date",
        "marriages",
        ["tree_id", "spouse_a_id", "spouse_b_id", "married_at"],
    )
    op.drop_index("ix_marriages_deleted_at", table_name="marriages")
    op.drop_column("marriages", "deleted_at")
