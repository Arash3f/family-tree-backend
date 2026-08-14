"""Add bilingual descriptions to permissions

Revision ID: 0012_permission_descriptions
Revises: 0011_integrity_indexes
Create Date: 2026-08-13 20:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_permission_descriptions"
down_revision: Union[str, Sequence[str], None] = "0011_integrity_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "permissions",
        sa.Column(
            "description_en",
            sa.String(length=500),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "permissions",
        sa.Column(
            "description_fa",
            sa.String(length=500),
            nullable=False,
            server_default="",
        ),
    )


def downgrade() -> None:
    op.drop_column("permissions", "description_fa")
    op.drop_column("permissions", "description_en")
