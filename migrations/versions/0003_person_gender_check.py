"""Add person gender check constraint

Revision ID: 0003_person_gender
Revises: 0002_person_dates
Create Date: 2026-08-09 11:13:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003_person_gender"
down_revision: Union[str, Sequence[str], None] = "0002_person_dates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_person_gender",
        "persons",
        "gender IN ('male', 'female')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_person_gender", "persons", type_="check")
