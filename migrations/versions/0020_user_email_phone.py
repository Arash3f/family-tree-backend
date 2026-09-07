"""Add optional users.email and users.phone for public registration.

Revision ID: 0020_user_email_phone
Revises: 0019_soft_delete_mtt
Create Date: 2026-09-07 10:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020_user_email_phone"
down_revision: Union[str, Sequence[str], None] = "0019_soft_delete_mtt"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(length=32), nullable=True))
    op.create_unique_constraint("uq_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_column("users", "phone")
    op.drop_column("users", "email")
