"""Add users.paid_until: the last day a paid plan covers.

Revision ID: 0024_user_paid_until
Revises: 0023_user_preferences
Create Date: 2026-10-27 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024_user_paid_until"
down_revision: Union[str, Sequence[str], None] = "0023_user_preferences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable on purpose: every existing paid account keeps a plan that never
    # lapses, exactly as before this column existed.
    op.add_column("users", sa.Column("paid_until", sa.Date(), nullable=True))
    op.create_index("ix_users_paid_until", "users", ["paid_until"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_paid_until", table_name="users")
    op.drop_column("users", "paid_until")
