"""Add users.preferred_locale and users.preferred_theme.

Revision ID: 0023_user_preferences
Revises: 0022_user_is_active
Create Date: 2026-09-21 18:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023_user_preferences"
down_revision: Union[str, Sequence[str], None] = "0022_user_is_active"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("preferred_locale", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("preferred_theme", sa.String(length=16), nullable=True),
    )
    op.create_check_constraint(
        "ck_users_preferred_locale",
        "users",
        "preferred_locale IS NULL OR preferred_locale IN ('en', 'fa')",
    )
    op.create_check_constraint(
        "ck_users_preferred_theme",
        "users",
        "preferred_theme IS NULL OR preferred_theme IN ('light', 'dark', 'system')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_preferred_theme", "users", type_="check")
    op.drop_constraint("ck_users_preferred_locale", "users", type_="check")
    op.drop_column("users", "preferred_theme")
    op.drop_column("users", "preferred_locale")
