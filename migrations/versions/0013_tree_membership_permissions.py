"""Add per-membership tree access permissions

Revision ID: 0013_tree_membership_permissions
Revises: 0012_permission_descriptions, 0012_user_fullname
Create Date: 2026-08-13 21:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_tree_membership_permissions"
down_revision: Union[str, Sequence[str], None] = (
    "0012_permission_descriptions",
    "0012_user_fullname",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tree_memberships",
        sa.Column(
            "permissions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[\"view\"]'::jsonb"),
        ),
    )
    # Preserve prior behavior for existing members (full access).
    op.execute(
        sa.text(
            """
            UPDATE tree_memberships
            SET permissions = '["view", "edit", "add_persons"]'::jsonb
            """
        )
    )


def downgrade() -> None:
    op.drop_column("tree_memberships", "permissions")
