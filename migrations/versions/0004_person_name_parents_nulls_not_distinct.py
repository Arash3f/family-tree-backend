"""Treat NULL parents as equal in person name uniqueness

Revision ID: 0004_person_name_unique
Revises: 0003_person_gender
Create Date: 2026-08-09 11:14:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0004_person_name_unique"
down_revision: Union[str, Sequence[str], None] = "0003_person_gender"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_person_name_parents", "persons", type_="unique")
    op.create_unique_constraint(
        "uq_person_name_parents",
        "persons",
        ["name", "father_id", "mother_id"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_constraint("uq_person_name_parents", "persons", type_="unique")
    op.create_unique_constraint(
        "uq_person_name_parents",
        "persons",
        ["name", "father_id", "mother_id"],
    )
