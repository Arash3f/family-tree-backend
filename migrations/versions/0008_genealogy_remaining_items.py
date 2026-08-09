"""Person soft-delete, genealogy fields, and marriage spouse model

Revision ID: 0008_genealogy_complete
Revises: 0007_parent_links
Create Date: 2026-08-09 11:48:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_genealogy_complete"
down_revision: Union[str, Sequence[str], None] = "0007_parent_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Person soft-delete + genealogy fields ---
    op.add_column(
        "persons",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("persons", sa.Column("family_name", sa.String(), nullable=True))
    op.add_column("persons", sa.Column("birth_place", sa.String(), nullable=True))
    op.add_column("persons", sa.Column("death_place", sa.String(), nullable=True))
    op.add_column("persons", sa.Column("notes", sa.String(), nullable=True))
    op.create_index(
        "ix_persons_deleted_at",
        "persons",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_persons_active_not_deleted",
        "persons",
        ["id"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_index("uq_person_name_marriage", table_name="persons")
    op.create_index(
        "uq_person_name_marriage",
        "persons",
        ["name", "marriage_id"],
        unique=True,
        postgresql_where=sa.text("marriage_id IS NOT NULL AND deleted_at IS NULL"),
    )

    # --- Marriage: drop monogamy + rename spouses + constraints ---
    op.drop_index("uq_active_marriage_husband", table_name="marriages")
    op.drop_index("uq_active_marriage_wife", table_name="marriages")
    op.drop_index("ix_marriage_husband_wife", table_name="marriages")
    op.drop_index("ix_marriages_husband_id", table_name="marriages")
    op.drop_index("ix_marriages_wife_id", table_name="marriages")
    op.drop_constraint("uq_marriage_couple_date", "marriages", type_="unique")
    op.drop_constraint("ck_marriage_no_self_marriage", "marriages", type_="check")
    op.drop_constraint("marriages_husband_id_fkey", "marriages", type_="foreignkey")
    op.drop_constraint("marriages_wife_id_fkey", "marriages", type_="foreignkey")

    op.alter_column("marriages", "husband_id", new_column_name="spouse_a_id")
    op.alter_column("marriages", "wife_id", new_column_name="spouse_b_id")

    op.create_foreign_key(
        "marriages_spouse_a_id_fkey",
        "marriages",
        "persons",
        ["spouse_a_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "marriages_spouse_b_id_fkey",
        "marriages",
        "persons",
        ["spouse_b_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_marriage_couple_date",
        "marriages",
        ["spouse_a_id", "spouse_b_id", "married_at"],
    )
    op.create_check_constraint(
        "ck_marriage_no_self_marriage",
        "marriages",
        "spouse_a_id != spouse_b_id",
    )
    op.create_check_constraint(
        "ck_marriage_divorce_after_married",
        "marriages",
        "divorced_at IS NULL OR divorced_at >= married_at",
    )
    op.create_index(
        "ix_marriage_spouses",
        "marriages",
        ["spouse_a_id", "spouse_b_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_marriages_spouse_a_id"), "marriages", ["spouse_a_id"], unique=False
    )
    op.create_index(
        op.f("ix_marriages_spouse_b_id"), "marriages", ["spouse_b_id"], unique=False
    )

    # Refresh parent-link marriage compatibility to use spouse columns
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_parent_link_rules()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
          biological_count integer;
          origin_marriage_id uuid;
          spouse_a uuid;
          spouse_b uuid;
        BEGIN
          IF EXISTS (
            WITH RECURSIVE ancestors AS (
              SELECT pl.parent_id AS id
              FROM parent_links AS pl
              WHERE pl.child_id = NEW.parent_id
              UNION
              SELECT pl.parent_id
              FROM parent_links AS pl
              INNER JOIN ancestors AS a ON pl.child_id = a.id
            )
            SELECT 1 FROM ancestors WHERE id = NEW.child_id
          ) THEN
            RAISE EXCEPTION 'parent assignment creates a cycle'
              USING ERRCODE = 'check_violation';
          END IF;

          IF NEW.relationship_type = 'biological' THEN
            SELECT COUNT(*) INTO biological_count
            FROM parent_links
            WHERE child_id = NEW.child_id
              AND relationship_type = 'biological'
              AND id IS DISTINCT FROM NEW.id;

            IF biological_count >= 2 THEN
              RAISE EXCEPTION 'child cannot have more than two biological parents'
                USING ERRCODE = 'check_violation';
            END IF;
          END IF;

          SELECT marriage_id INTO origin_marriage_id
          FROM persons
          WHERE id = NEW.child_id;

          IF origin_marriage_id IS NOT NULL AND NEW.relationship_type = 'biological' THEN
            SELECT spouse_a_id, spouse_b_id INTO spouse_a, spouse_b
            FROM marriages
            WHERE id = origin_marriage_id;

            IF NEW.parent_id IS DISTINCT FROM spouse_a
               AND NEW.parent_id IS DISTINCT FROM spouse_b THEN
              RAISE EXCEPTION 'biological parent must belong to origin marriage spouses'
                USING ERRCODE = 'check_violation';
            END IF;
          END IF;

          RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_person_marriage_parent_rules()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
          spouse_a uuid;
          spouse_b uuid;
          bad_parent uuid;
        BEGIN
          IF NEW.marriage_id IS NULL THEN
            RETURN NEW;
          END IF;

          SELECT spouse_a_id, spouse_b_id INTO spouse_a, spouse_b
          FROM marriages
          WHERE id = NEW.marriage_id;

          SELECT pl.parent_id INTO bad_parent
          FROM parent_links AS pl
          WHERE pl.child_id = NEW.id
            AND pl.relationship_type = 'biological'
            AND pl.parent_id IS DISTINCT FROM spouse_a
            AND pl.parent_id IS DISTINCT FROM spouse_b
          LIMIT 1;

          IF bad_parent IS NOT NULL THEN
            RAISE EXCEPTION 'biological parent must belong to origin marriage spouses'
              USING ERRCODE = 'check_violation';
          END IF;

          RETURN NEW;
        END;
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_parent_link_rules()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
          biological_count integer;
          origin_marriage_id uuid;
          spouse_a uuid;
          spouse_b uuid;
        BEGIN
          IF EXISTS (
            WITH RECURSIVE ancestors AS (
              SELECT pl.parent_id AS id
              FROM parent_links AS pl
              WHERE pl.child_id = NEW.parent_id
              UNION
              SELECT pl.parent_id
              FROM parent_links AS pl
              INNER JOIN ancestors AS a ON pl.child_id = a.id
            )
            SELECT 1 FROM ancestors WHERE id = NEW.child_id
          ) THEN
            RAISE EXCEPTION 'parent assignment creates a cycle'
              USING ERRCODE = 'check_violation';
          END IF;

          IF NEW.relationship_type = 'biological' THEN
            SELECT COUNT(*) INTO biological_count
            FROM parent_links
            WHERE child_id = NEW.child_id
              AND relationship_type = 'biological'
              AND id IS DISTINCT FROM NEW.id;
            IF biological_count >= 2 THEN
              RAISE EXCEPTION 'child cannot have more than two biological parents'
                USING ERRCODE = 'check_violation';
            END IF;
          END IF;

          SELECT marriage_id INTO origin_marriage_id FROM persons WHERE id = NEW.child_id;
          IF origin_marriage_id IS NOT NULL AND NEW.relationship_type = 'biological' THEN
            SELECT husband_id, wife_id INTO spouse_a, spouse_b
            FROM marriages WHERE id = origin_marriage_id;
            IF NEW.parent_id IS DISTINCT FROM spouse_a
               AND NEW.parent_id IS DISTINCT FROM spouse_b THEN
              RAISE EXCEPTION 'biological parent must belong to origin marriage spouses'
                USING ERRCODE = 'check_violation';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$;
        """
    )

    op.drop_index(op.f("ix_marriages_spouse_b_id"), table_name="marriages")
    op.drop_index(op.f("ix_marriages_spouse_a_id"), table_name="marriages")
    op.drop_index("ix_marriage_spouses", table_name="marriages")
    op.drop_constraint("ck_marriage_divorce_after_married", "marriages", type_="check")
    op.drop_constraint("ck_marriage_no_self_marriage", "marriages", type_="check")
    op.drop_constraint("uq_marriage_couple_date", "marriages", type_="unique")
    op.drop_constraint("marriages_spouse_b_id_fkey", "marriages", type_="foreignkey")
    op.drop_constraint("marriages_spouse_a_id_fkey", "marriages", type_="foreignkey")
    op.alter_column("marriages", "spouse_a_id", new_column_name="husband_id")
    op.alter_column("marriages", "spouse_b_id", new_column_name="wife_id")
    op.create_foreign_key(
        "marriages_husband_id_fkey", "marriages", "persons", ["husband_id"], ["id"]
    )
    op.create_foreign_key(
        "marriages_wife_id_fkey", "marriages", "persons", ["wife_id"], ["id"]
    )
    op.create_unique_constraint(
        "uq_marriage_couple_date",
        "marriages",
        ["husband_id", "wife_id", "married_at"],
    )
    op.create_check_constraint(
        "ck_marriage_no_self_marriage", "marriages", "husband_id != wife_id"
    )
    op.create_index(
        "ix_marriage_husband_wife", "marriages", ["husband_id", "wife_id"], unique=False
    )
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

    op.drop_index("ix_persons_active_not_deleted", table_name="persons")
    op.drop_index("ix_persons_deleted_at", table_name="persons")
    op.drop_column("persons", "notes")
    op.drop_column("persons", "death_place")
    op.drop_column("persons", "birth_place")
    op.drop_column("persons", "family_name")
    op.drop_column("persons", "deleted_at")
