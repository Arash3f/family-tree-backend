"""Add required users.fullname, backfill from username

Revision ID: 0012_user_fullname
Revises: 0011_integrity_indexes
Create Date: 2026-08-13 20:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_user_fullname"
down_revision: Union[str, Sequence[str], None] = "0011_integrity_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("fullname", sa.String(length=100), nullable=True))
    op.execute(sa.text("UPDATE users SET fullname = username WHERE fullname IS NULL"))
    op.alter_column("users", "fullname", existing_type=sa.String(length=100), nullable=False)


def downgrade() -> None:
    op.drop_column("users", "fullname")
