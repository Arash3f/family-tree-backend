"""Add users.is_active for soft-delete / deactivation.

Revision ID: 0022_user_is_active
Revises: 0021_drop_name_marriage_uq
Create Date: 2026-09-13 19:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022_user_is_active"
down_revision: Union[str, Sequence[str], None] = "0021_drop_name_marriage_uq"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_active")
