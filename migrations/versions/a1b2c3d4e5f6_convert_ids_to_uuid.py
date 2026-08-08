"""convert entity ids from integer to uuid

WARNING: This migration is DESTRUCTIVE. It drops and recreates all application
tables. Do not run against an environment that contains data you need to keep.
Prefer a fresh database or restore from backup after upgrading.

Revision ID: a1b2c3d4e5f6
Revises: 468ab146bc68
Create Date: 2026-07-26 11:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "468ab146bc68"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Recreate schema with UUID primary/foreign keys (destructive)."""
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS role_permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS marriages CASCADE")
    op.execute("DROP TABLE IF EXISTS roles CASCADE")
    op.execute("DROP TABLE IF EXISTS persons CASCADE")
    op.execute("DROP TABLE IF EXISTS permissions CASCADE")

    op.create_table(
        "permissions",
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)

    op.create_table(
        "persons",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("gender", sa.String(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("death_date", sa.Date(), nullable=True),
        sa.Column("father_id", sa.Uuid(), nullable=True),
        sa.Column("mother_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["father_id"], ["persons.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mother_id"], ["persons.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "name", "father_id", "mother_id", name="uq_person_name_parents"
        ),
    )
    op.create_index(op.f("ix_persons_id"), "persons", ["id"], unique=False)

    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)

    op.create_table(
        "marriages",
        sa.Column("husband_id", sa.Uuid(), nullable=False),
        sa.Column("wife_id", sa.Uuid(), nullable=False),
        sa.Column("married_at", sa.Date(), nullable=False),
        sa.Column("divorced_at", sa.Date(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "husband_id != wife_id", name="ck_marriage_no_self_marriage"
        ),
        sa.ForeignKeyConstraint(["husband_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["wife_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "husband_id", "wife_id", "married_at", name="uq_marriage_couple_date"
        ),
    )
    op.create_index(
        "ix_marriage_husband_wife", "marriages", ["husband_id", "wife_id"], unique=False
    )
    op.create_index(
        op.f("ix_marriages_husband_id"), "marriages", ["husband_id"], unique=False
    )
    op.create_index(op.f("ix_marriages_id"), "marriages", ["id"], unique=False)
    op.create_index(
        op.f("ix_marriages_wife_id"), "marriages", ["wife_id"], unique=False
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permissions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.create_table(
        "users",
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)


def downgrade() -> None:
    """Recreate schema with integer primary/foreign keys (destructive)."""
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS role_permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS marriages CASCADE")
    op.execute("DROP TABLE IF EXISTS roles CASCADE")
    op.execute("DROP TABLE IF EXISTS persons CASCADE")
    op.execute("DROP TABLE IF EXISTS permissions CASCADE")

    op.create_table(
        "permissions",
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)

    op.create_table(
        "persons",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("gender", sa.String(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("father_id", sa.Integer(), nullable=True),
        sa.Column("mother_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["father_id"], ["persons.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mother_id"], ["persons.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "name", "father_id", "mother_id", name="uq_person_name_parents"
        ),
    )
    op.create_index(op.f("ix_persons_id"), "persons", ["id"], unique=False)

    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)

    op.create_table(
        "marriages",
        sa.Column("husband_id", sa.Integer(), nullable=False),
        sa.Column("wife_id", sa.Integer(), nullable=False),
        sa.Column("married_at", sa.Date(), nullable=False),
        sa.Column("divorced_at", sa.Date(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "husband_id != wife_id", name="ck_marriage_no_self_marriage"
        ),
        sa.ForeignKeyConstraint(["husband_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["wife_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "husband_id", "wife_id", "married_at", name="uq_marriage_couple_date"
        ),
    )
    op.create_index(
        "ix_marriage_husband_wife", "marriages", ["husband_id", "wife_id"], unique=False
    )
    op.create_index(
        op.f("ix_marriages_husband_id"), "marriages", ["husband_id"], unique=False
    )
    op.create_index(op.f("ix_marriages_id"), "marriages", ["id"], unique=False)
    op.create_index(
        op.f("ix_marriages_wife_id"), "marriages", ["wife_id"], unique=False
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permissions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.create_table(
        "users",
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
