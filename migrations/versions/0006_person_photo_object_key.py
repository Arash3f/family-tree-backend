"""Add photo_object_key to persons

Revision ID: 0006_person_photo
Revises: 0005_person_parents
Create Date: 2026-08-09 11:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_person_photo"
down_revision: Union[str, Sequence[str], None] = "0005_person_parents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column("photo_object_key", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("persons", "photo_object_key")
