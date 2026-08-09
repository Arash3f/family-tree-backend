"""Enforce person parent integrity rules

Revision ID: 0005_person_parents
Revises: 0004_person_name_unique
Create Date: 2026-08-09 11:16:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0005_person_parents"
down_revision: Union[str, Sequence[str], None] = "0004_person_name_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PARENT_RULES_FUNCTION = """
CREATE OR REPLACE FUNCTION enforce_person_parent_rules()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  parent_gender text;
BEGIN
  IF NEW.father_id IS NOT NULL THEN
    SELECT gender INTO parent_gender FROM persons WHERE id = NEW.father_id;
    IF parent_gender IS DISTINCT FROM 'male' THEN
      RAISE EXCEPTION 'father gender must be male'
        USING ERRCODE = 'check_violation';
    END IF;

    IF EXISTS (
      WITH RECURSIVE ancestors AS (
        SELECT p.id, p.father_id, p.mother_id
        FROM persons AS p
        WHERE p.id = NEW.father_id
        UNION ALL
        SELECT p.id, p.father_id, p.mother_id
        FROM persons AS p
        INNER JOIN ancestors AS a
          ON p.id = a.father_id OR p.id = a.mother_id
      )
      SELECT 1 FROM ancestors WHERE id = NEW.id
    ) THEN
      RAISE EXCEPTION 'father assignment creates a cycle'
        USING ERRCODE = 'check_violation';
    END IF;
  END IF;

  IF NEW.mother_id IS NOT NULL THEN
    SELECT gender INTO parent_gender FROM persons WHERE id = NEW.mother_id;
    IF parent_gender IS DISTINCT FROM 'female' THEN
      RAISE EXCEPTION 'mother gender must be female'
        USING ERRCODE = 'check_violation';
    END IF;

    IF EXISTS (
      WITH RECURSIVE ancestors AS (
        SELECT p.id, p.father_id, p.mother_id
        FROM persons AS p
        WHERE p.id = NEW.mother_id
        UNION ALL
        SELECT p.id, p.father_id, p.mother_id
        FROM persons AS p
        INNER JOIN ancestors AS a
          ON p.id = a.father_id OR p.id = a.mother_id
      )
      SELECT 1 FROM ancestors WHERE id = NEW.id
    ) THEN
      RAISE EXCEPTION 'mother assignment creates a cycle'
        USING ERRCODE = 'check_violation';
    END IF;
  END IF;

  RETURN NEW;
END;
$$;
"""


def upgrade() -> None:
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

    op.execute(PARENT_RULES_FUNCTION)
    op.execute(
        """
        CREATE TRIGGER trg_person_parent_rules
        BEFORE INSERT OR UPDATE OF father_id, mother_id
        ON persons
        FOR EACH ROW
        EXECUTE FUNCTION enforce_person_parent_rules();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_person_parent_rules ON persons")
    op.execute("DROP FUNCTION IF EXISTS enforce_person_parent_rules()")
    op.drop_constraint("ck_person_distinct_parents", "persons", type_="check")
    op.drop_constraint("ck_person_no_self_mother", "persons", type_="check")
    op.drop_constraint("ck_person_no_self_father", "persons", type_="check")
