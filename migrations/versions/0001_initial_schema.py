"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-08 22:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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

    op.create_table(
        "user_sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_id", sa.Uuid(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["replaced_by_id"], ["user_sessions.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_sessions_expires_at"),
        "user_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(op.f("ix_user_sessions_id"), "user_sessions", ["id"], unique=False)
    op.create_index(
        op.f("ix_user_sessions_refresh_token_hash"),
        "user_sessions",
        ["refresh_token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_index(
        op.f("ix_user_sessions_refresh_token_hash"), table_name="user_sessions"
    )
    op.drop_index(op.f("ix_user_sessions_id"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_expires_at"), table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_index("uq_active_marriage_wife", table_name="marriages")
    op.drop_index("uq_active_marriage_husband", table_name="marriages")
    op.drop_index(op.f("ix_marriages_wife_id"), table_name="marriages")
    op.drop_index(op.f("ix_marriages_id"), table_name="marriages")
    op.drop_index(op.f("ix_marriages_husband_id"), table_name="marriages")
    op.drop_index("ix_marriage_husband_wife", table_name="marriages")
    op.drop_table("marriages")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")
    op.drop_index(op.f("ix_persons_id"), table_name="persons")
    op.drop_table("persons")
    op.drop_index(op.f("ix_permissions_id"), table_name="permissions")
    op.drop_table("permissions")
