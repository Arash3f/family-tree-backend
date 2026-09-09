"""Allow namesake siblings under the same marriage.

Revision ID: 0021_drop_name_marriage_uq
Revises: 0020_user_email_phone
Create Date: 2026-09-07 13:30:00.000000

Keep the revision id at or under 32 characters so it fits Alembic's default
``alembic_version.version_num`` column.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021_drop_name_marriage_uq"
down_revision: Union[str, Sequence[str], None] = "0020_user_email_phone"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("uq_person_tree_name_marriage", table_name="persons")


def downgrade() -> None:
    op.create_index(
        "uq_person_tree_name_marriage",
        "persons",
        ["tree_id", "name", "marriage_id"],
        unique=True,
        postgresql_where=sa.text("marriage_id IS NOT NULL AND deleted_at IS NULL"),
    )
