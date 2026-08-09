"""Postgres DDL for parent_links integrity (used by migrations and tests)."""

PARENT_LINK_RULES_FUNCTION = """
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

PERSON_MARRIAGE_RULES_FUNCTION = """
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

PARENT_LINK_TRIGGER = """
CREATE TRIGGER trg_parent_link_rules
BEFORE INSERT OR UPDATE OF child_id, parent_id, relationship_type
ON parent_links
FOR EACH ROW
EXECUTE FUNCTION enforce_parent_link_rules();
"""

PERSON_MARRIAGE_TRIGGER = """
CREATE TRIGGER trg_person_marriage_parent_rules
BEFORE INSERT OR UPDATE OF marriage_id
ON persons
FOR EACH ROW
EXECUTE FUNCTION enforce_person_marriage_parent_rules();
"""


def install_parent_integrity_ddl(connection) -> None:
    connection.exec_driver_sql(PARENT_LINK_RULES_FUNCTION)
    connection.exec_driver_sql(PERSON_MARRIAGE_RULES_FUNCTION)
    connection.exec_driver_sql(
        "DROP TRIGGER IF EXISTS trg_parent_link_rules ON parent_links"
    )
    connection.exec_driver_sql(PARENT_LINK_TRIGGER)
    connection.exec_driver_sql(
        "DROP TRIGGER IF EXISTS trg_person_marriage_parent_rules ON persons"
    )
    connection.exec_driver_sql(PERSON_MARRIAGE_TRIGGER)
