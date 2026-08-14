"""Drop ticket_manage; reply is now the support permission.

Revision ID: 0015_drop_ticket_manage
Revises: 0014_merge_ticket_and_membership
Create Date: 2026-08-14 00:31:00.000000

"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0015_drop_ticket_manage"
down_revision: Union[str, Sequence[str], None] = "0014_merge_ticket_and_membership"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    create_id = conn.execute(
        sa.text("SELECT id FROM permissions WHERE name = 'ticket_create'")
    ).scalar()
    reply_id = conn.execute(
        sa.text("SELECT id FROM permissions WHERE name = 'ticket_reply'")
    ).scalar()
    manage_id = conn.execute(
        sa.text("SELECT id FROM permissions WHERE name = 'ticket_manage'")
    ).scalar()

    if create_id and reply_id:
        # Old bundle granted reply with create. Those roles were requesters,
        # not support, unless they also had ticket_manage.
        if manage_id:
            conn.execute(
                sa.text(
                    """
                    DELETE FROM role_permissions rp
                    WHERE rp.permission_id = :reply_id
                      AND EXISTS (
                        SELECT 1 FROM role_permissions created
                        WHERE created.role_id = rp.role_id
                          AND created.permission_id = :create_id
                      )
                      AND NOT EXISTS (
                        SELECT 1 FROM role_permissions managed
                        WHERE managed.role_id = rp.role_id
                          AND managed.permission_id = :manage_id
                      )
                    """
                ),
                {
                    "reply_id": reply_id,
                    "create_id": create_id,
                    "manage_id": manage_id,
                },
            )
        else:
            conn.execute(
                sa.text(
                    """
                    DELETE FROM role_permissions rp
                    WHERE rp.permission_id = :reply_id
                      AND EXISTS (
                        SELECT 1 FROM role_permissions created
                        WHERE created.role_id = rp.role_id
                          AND created.permission_id = :create_id
                      )
                    """
                ),
                {"reply_id": reply_id, "create_id": create_id},
            )

    if manage_id and reply_id:
        conn.execute(
            sa.text(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT rp.role_id, :reply_id
                FROM role_permissions rp
                WHERE rp.permission_id = :manage_id
                  AND NOT EXISTS (
                    SELECT 1 FROM role_permissions existing
                    WHERE existing.role_id = rp.role_id
                      AND existing.permission_id = :reply_id
                  )
                """
            ),
            {"reply_id": reply_id, "manage_id": manage_id},
        )

    if manage_id:
        conn.execute(
            sa.text("DELETE FROM permissions WHERE id = :id"),
            {"id": manage_id},
        )


def downgrade() -> None:
    conn = op.get_bind()
    manage_id = uuid4()
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions (
                id, name, description_en, description_fa, created_at, updated_at
            )
            VALUES (
                :id,
                'ticket_manage',
                'Reply as support, change ticket status, and manage the queue.',
                'پاسخ به‌عنوان پشتیبان، تغییر وضعیت تیکت و مدیریت صف.',
                NOW(),
                NOW()
            )
            """
        ),
        {"id": manage_id},
    )

    reply_id = conn.execute(
        sa.text("SELECT id FROM permissions WHERE name = 'ticket_reply'")
    ).scalar()
    create_id = conn.execute(
        sa.text("SELECT id FROM permissions WHERE name = 'ticket_create'")
    ).scalar()

    if reply_id:
        conn.execute(
            sa.text(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT rp.role_id, :manage_id
                FROM role_permissions rp
                WHERE rp.permission_id = :reply_id
                  AND NOT EXISTS (
                    SELECT 1 FROM role_permissions existing
                    WHERE existing.role_id = rp.role_id
                      AND existing.permission_id = :manage_id
                  )
                """
            ),
            {"manage_id": manage_id, "reply_id": reply_id},
        )

    if create_id and reply_id:
        conn.execute(
            sa.text(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT rp.role_id, :reply_id
                FROM role_permissions rp
                WHERE rp.permission_id = :create_id
                  AND NOT EXISTS (
                    SELECT 1 FROM role_permissions existing
                    WHERE existing.role_id = rp.role_id
                      AND existing.permission_id = :reply_id
                  )
                """
            ),
            {"reply_id": reply_id, "create_id": create_id},
        )
