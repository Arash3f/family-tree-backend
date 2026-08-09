"""Replace father/mother columns with parent_links and marriage_id

Revision ID: 0007_parent_links
Revises: 0006_person_photo
Create Date: 2026-08-09 11:34:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.infrastructure.database.parent_integrity_ddl import (
    PARENT_LINK_RULES_FUNCTION,
    PARENT_LINK_TRIGGER,
    PERSON_MARRIAGE_RULES_FUNCTION,
    PERSON_MARRIAGE_TRIGGER,
)

revision: str = "0007_parent_links"
down_revision: Union[str, Sequence[str], None] = "0006_person_photo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "parent_links",
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_type", sa.String(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("child_id != parent_id", name="ck_parent_link_no_self"),
        sa.CheckConstraint(
            "relationship_type IN ('biological', 'adoptive', 'step')",
            name="ck_parent_link_relationship_type",
        ),
        sa.ForeignKeyConstraint(["child_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["persons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "child_id", "parent_id", name="uq_parent_link_child_parent"
        ),
    )
    op.create_index(op.f("ix_parent_links_child_id"), "parent_links", ["child_id"])
    op.create_index(op.f("ix_parent_links_id"), "parent_links", ["id"])
    op.create_index(op.f("ix_parent_links_parent_id"), "parent_links", ["parent_id"])

    op.execute(
        """
        INSERT INTO parent_links (
            id, child_id, parent_id, relationship_type, created_at, updated_at
        )
        SELECT gen_random_uuid(), id, father_id, 'biological', NOW(), NOW()
        FROM persons
        WHERE father_id IS NOT NULL
        """
    )
    op.execute(
        """
        INSERT INTO parent_links (
            id, child_id, parent_id, relationship_type, created_at, updated_at
        )
        SELECT gen_random_uuid(), id, mother_id, 'biological', NOW(), NOW()
        FROM persons
        WHERE mother_id IS NOT NULL
        """
    )

    op.execute("DROP TRIGGER IF EXISTS trg_person_parent_rules ON persons")
    op.execute("DROP FUNCTION IF EXISTS enforce_person_parent_rules()")
    op.drop_constraint("ck_person_distinct_parents", "persons", type_="check")
    op.drop_constraint("ck_person_no_self_mother", "persons", type_="check")
    op.drop_constraint("ck_person_no_self_father", "persons", type_="check")
    op.drop_constraint("uq_person_name_parents", "persons", type_="unique")
    op.drop_constraint("persons_father_id_fkey", "persons", type_="foreignkey")
    op.drop_constraint("persons_mother_id_fkey", "persons", type_="foreignkey")
    op.drop_column("persons", "father_id")
    op.drop_column("persons", "mother_id")

    op.add_column("persons", sa.Column("marriage_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_persons_marriage_id"), "persons", ["marriage_id"])
    op.create_foreign_key(
        "persons_marriage_id_fkey",
        "persons",
        "marriages",
        ["marriage_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_person_name_marriage",
        "persons",
        ["name", "marriage_id"],
        postgresql_nulls_not_distinct=True,
    )

    op.execute(PARENT_LINK_RULES_FUNCTION)
    op.execute(PARENT_LINK_TRIGGER)
    op.execute(PERSON_MARRIAGE_RULES_FUNCTION)
    op.execute(PERSON_MARRIAGE_TRIGGER)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_person_marriage_parent_rules ON persons")
    op.execute("DROP FUNCTION IF EXISTS enforce_person_marriage_parent_rules()")
    op.execute("DROP TRIGGER IF EXISTS trg_parent_link_rules ON parent_links")
    op.execute("DROP FUNCTION IF EXISTS enforce_parent_link_rules()")

    op.drop_constraint("uq_person_name_marriage", "persons", type_="unique")
    op.drop_constraint("persons_marriage_id_fkey", "persons", type_="foreignkey")
    op.drop_index(op.f("ix_persons_marriage_id"), table_name="persons")
    op.drop_column("persons", "marriage_id")

    op.add_column("persons", sa.Column("father_id", sa.Uuid(), nullable=True))
    op.add_column("persons", sa.Column("mother_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "persons_father_id_fkey",
        "persons",
        "persons",
        ["father_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "persons_mother_id_fkey",
        "persons",
        "persons",
        ["mother_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        """
        UPDATE persons AS p
        SET father_id = pl.parent_id
        FROM (
            SELECT DISTINCT ON (child_id) child_id, parent_id
            FROM parent_links
            WHERE relationship_type = 'biological'
            ORDER BY child_id, created_at
        ) AS pl
        WHERE p.id = pl.child_id
          AND p.father_id IS NULL
        """
    )

    op.create_unique_constraint(
        "uq_person_name_parents",
        "persons",
        ["name", "father_id", "mother_id"],
        postgresql_nulls_not_distinct=True,
    )
    op.create_check_constraint(
        "ck_person_no_self_father",
        "persons",
        "father_id IS NULL OR father_id != id",
    )
    op.create_check_constraint(
        "ck_person_no_self_mother",
        "persons",
        "mother_id IS NULL OR mother_id != id",
    )
    op.create_check_constraint(
        "ck_person_distinct_parents",
        "persons",
        "father_id IS NULL OR mother_id IS NULL OR father_id != mother_id",
    )

    op.drop_index(op.f("ix_parent_links_parent_id"), table_name="parent_links")
    op.drop_index(op.f("ix_parent_links_id"), table_name="parent_links")
    op.drop_index(op.f("ix_parent_links_child_id"), table_name="parent_links")
    op.drop_table("parent_links")
