"""Add person death_date >= birth_date check

Revision ID: 0002_person_dates
Revises: 0001_initial
Create Date: 2026-08-09 11:12:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_person_dates"
down_revision: Union[str, Sequence[str], None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_person_death_after_birth",
        "persons",
        "death_date IS NULL OR birth_date IS NULL OR death_date >= birth_date",
    )


def downgrade() -> None:
    op.drop_constraint("ck_person_death_after_birth", "persons", type_="check")
