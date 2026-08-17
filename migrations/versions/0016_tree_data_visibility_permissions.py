"""Add per-membership visibility permissions for sensitive tree data.

Revision ID: 0016_tree_data_visibility
Revises: 0015_drop_ticket_manage
Create Date: 2026-08-16 10:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016_tree_data_visibility"
down_revision: Union[str, Sequence[str], None] = "0015_drop_ticket_manage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing memberships could already see these values. Preserve that
    # behavior; newly created memberships still start with only "view".
    op.execute(
        sa.text(
            """
            UPDATE tree_memberships
            SET permissions = permissions
                || '[
                    "view_birth_date",
                    "view_marriage_date",
                    "view_photo"
                ]'::jsonb
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE tree_memberships
            SET permissions = permissions
                - 'view_birth_date'
                - 'view_marriage_date'
                - 'view_photo'
            """
        )
    )
