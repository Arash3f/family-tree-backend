"""Family trees, memberships, and tree-scoped genealogy

Revision ID: 0009_family_trees
Revises: 0008_genealogy_complete
Create Date: 2026-08-09 12:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_family_trees"
down_revision: Union[str, Sequence[str], None] = "0008_genealogy_complete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "family_trees",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_family_trees_id", "family_trees", ["id"], unique=False)
    op.create_index(
        "ix_family_trees_owner_user_id",
        "family_trees",
        ["owner_user_id"],
        unique=False,
    )

    op.create_table(
        "tree_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tree_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('owner', 'member')", name="ck_tree_membership_role"),
        sa.ForeignKeyConstraint(
            ["tree_id"], ["family_trees.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tree_id", "user_id", name="uq_tree_membership_tree_user"
        ),
    )
    op.create_index(
        "ix_tree_memberships_id", "tree_memberships", ["id"], unique=False
    )
    op.create_index(
        "ix_tree_memberships_tree_id",
        "tree_memberships",
        ["tree_id"],
        unique=False,
    )
    op.create_index(
        "ix_tree_memberships_user_id",
        "tree_memberships",
        ["user_id"],
        unique=False,
    )

    op.add_column("persons", sa.Column("tree_id", sa.Uuid(), nullable=True))
    op.add_column("marriages", sa.Column("tree_id", sa.Uuid(), nullable=True))

    # Backfill: one default tree owned by the first user (typically admin).
    conn = op.get_bind()
    user_id = conn.execute(sa.text("SELECT id FROM users ORDER BY created_at LIMIT 1")).scalar()
    if user_id is not None:
        tree_id = conn.execute(
            sa.text(
                """
                INSERT INTO family_trees (id, name, owner_user_id, created_at, updated_at)
                VALUES (gen_random_uuid(), 'Default Family Tree', :owner_id, NOW(), NOW())
                RETURNING id
                """
            ),
            {"owner_id": user_id},
        ).scalar()
        conn.execute(
            sa.text(
                """
                INSERT INTO tree_memberships
                    (id, tree_id, user_id, role, created_at, updated_at)
                VALUES
                    (gen_random_uuid(), :tree_id, :user_id, 'owner', NOW(), NOW())
                """
            ),
            {"tree_id": tree_id, "user_id": user_id},
        )
        conn.execute(
            sa.text("UPDATE persons SET tree_id = :tree_id WHERE tree_id IS NULL"),
            {"tree_id": tree_id},
        )
        conn.execute(
            sa.text("UPDATE marriages SET tree_id = :tree_id WHERE tree_id IS NULL"),
            {"tree_id": tree_id},
        )
    else:
        # No users yet: create a placeholder tree only if genealogy rows exist.
        has_people = conn.execute(sa.text("SELECT 1 FROM persons LIMIT 1")).scalar()
        has_marriages = conn.execute(sa.text("SELECT 1 FROM marriages LIMIT 1")).scalar()
        if has_people or has_marriages:
            raise RuntimeError(
                "Cannot backfill tree_id: genealogy rows exist but no users found"
            )

    op.alter_column("persons", "tree_id", nullable=False)
    op.alter_column("marriages", "tree_id", nullable=False)

    op.create_foreign_key(
        "fk_persons_tree_id_family_trees",
        "persons",
        "family_trees",
        ["tree_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_persons_tree_id", "persons", ["tree_id"], unique=False)

    op.create_foreign_key(
        "fk_marriages_tree_id_family_trees",
        "marriages",
        "family_trees",
        ["tree_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_marriages_tree_id", "marriages", ["tree_id"], unique=False)

    op.drop_index("uq_person_name_marriage", table_name="persons")
    op.create_index(
        "uq_person_tree_name_marriage",
        "persons",
        ["tree_id", "name", "marriage_id"],
        unique=True,
        postgresql_where=sa.text(
            "marriage_id IS NOT NULL AND deleted_at IS NULL"
        ),
    )

    op.drop_constraint("uq_marriage_couple_date", "marriages", type_="unique")
    op.create_unique_constraint(
        "uq_marriage_tree_couple_date",
        "marriages",
        ["tree_id", "spouse_a_id", "spouse_b_id", "married_at"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_marriage_tree_couple_date", "marriages", type_="unique")
    op.create_unique_constraint(
        "uq_marriage_couple_date",
        "marriages",
        ["spouse_a_id", "spouse_b_id", "married_at"],
    )

    op.drop_index("uq_person_tree_name_marriage", table_name="persons")
    op.create_index(
        "uq_person_name_marriage",
        "persons",
        ["name", "marriage_id"],
        unique=True,
        postgresql_where=sa.text(
            "marriage_id IS NOT NULL AND deleted_at IS NULL"
        ),
    )

    op.drop_constraint("fk_marriages_tree_id_family_trees", "marriages", type_="foreignkey")
    op.drop_index("ix_marriages_tree_id", table_name="marriages")
    op.drop_column("marriages", "tree_id")

    op.drop_constraint("fk_persons_tree_id_family_trees", "persons", type_="foreignkey")
    op.drop_index("ix_persons_tree_id", table_name="persons")
    op.drop_column("persons", "tree_id")

    op.drop_index("ix_tree_memberships_user_id", table_name="tree_memberships")
    op.drop_index("ix_tree_memberships_tree_id", table_name="tree_memberships")
    op.drop_index("ix_tree_memberships_id", table_name="tree_memberships")
    op.drop_table("tree_memberships")

    op.drop_index("ix_family_trees_owner_user_id", table_name="family_trees")
    op.drop_index("ix_family_trees_id", table_name="family_trees")
    op.drop_table("family_trees")
