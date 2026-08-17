"""Add users.account_type (free/paid); existing users become paid.

Revision ID: 0018_user_account_type
Revises: 0017_tree_access_ops
Create Date: 2026-08-17 08:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018_user_account_type"
down_revision: Union[str, Sequence[str], None] = "0017_tree_access_ops"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "account_type",
            sa.String(length=20),
            nullable=False,
            server_default="free",
        ),
    )
    # Preserve unlimited access for accounts that already exist.
    op.execute(sa.text("UPDATE users SET account_type = 'paid'"))


def downgrade() -> None:
    op.drop_column("users", "account_type")
