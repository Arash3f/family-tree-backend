"""add unique indexes for active marriages

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-26 12:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_active_marriage_husband",
        "marriages",
        ["husband_id"],
        unique=True,
        postgresql_where=sa.text("divorced_at IS NULL"),
    )
    op.create_index(
        "uq_active_marriage_wife",
        "marriages",
        ["wife_id"],
        unique=True,
        postgresql_where=sa.text("divorced_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_active_marriage_wife", table_name="marriages")
    op.drop_index("uq_active_marriage_husband", table_name="marriages")
