"""Ticket status check, same-tree parent links, and hot-path partial indexes

Revision ID: 0011_integrity_indexes
Revises: 0010_tickets
Create Date: 2026-08-09 14:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.infrastructure.database.parent_integrity_ddl import (
    PARENT_LINK_RULES_FUNCTION,
)

revision: str = "0011_integrity_indexes"
down_revision: Union[str, Sequence[str], None] = "0010_tickets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# The pre-0011 body, kept here so the downgrade does not depend on the current
# contents of parent_integrity_ddl.py.
PARENT_LINK_RULES_WITHOUT_TREE_CHECK = """
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


def upgrade() -> None:
    # Ticket status was validated only by the Python enum, so anything writing
    # to the table directly could store an unknown state.
    op.create_check_constraint(
        "ck_ticket_status",
        "tickets",
        "status IN ('open', 'in_progress', 'closed')",
    )

    # Tree isolation is the security boundary of this schema; a parent link
    # spanning two trees would quietly join them in the graph.
    op.execute(PARENT_LINK_RULES_FUNCTION)

    op.create_index(
        "ix_marriage_active_spouse_a",
        "marriages",
        ["spouse_a_id"],
        unique=False,
        postgresql_where=sa.text("divorced_at IS NULL"),
    )
    op.create_index(
        "ix_marriage_active_spouse_b",
        "marriages",
        ["spouse_b_id"],
        unique=False,
        postgresql_where=sa.text("divorced_at IS NULL"),
    )
    op.create_index(
        "ix_user_sessions_active_by_user",
        "user_sessions",
        ["user_id"],
        unique=False,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    # Uniqueness on refresh_token_hash was a bare unique index, which the ORM
    # metadata expresses as a constraint. Swapping it keeps a schema built from
    # migrations identical to one built from the models.
    op.create_unique_constraint(
        "uq_user_sessions_refresh_token_hash",
        "user_sessions",
        ["refresh_token_hash"],
    )
    op.drop_index("ix_user_sessions_refresh_token_hash", table_name="user_sessions")


def downgrade() -> None:
    op.create_index(
        "ix_user_sessions_refresh_token_hash",
        "user_sessions",
        ["refresh_token_hash"],
        unique=True,
    )
    op.drop_constraint(
        "uq_user_sessions_refresh_token_hash", "user_sessions", type_="unique"
    )
    op.drop_index("ix_user_sessions_active_by_user", table_name="user_sessions")
    op.drop_index("ix_marriage_active_spouse_b", table_name="marriages")
    op.drop_index("ix_marriage_active_spouse_a", table_name="marriages")
    op.execute(PARENT_LINK_RULES_WITHOUT_TREE_CHECK)
    op.drop_constraint("ck_ticket_status", "tickets", type_="check")
