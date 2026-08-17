"""Replace coarse tree access with operation-level permissions.

Revision ID: 0017_tree_access_ops
Revises: 0016_tree_data_visibility
Create Date: 2026-08-17 08:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017_tree_access_ops"
down_revision: Union[str, Sequence[str], None] = "0016_tree_data_visibility"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep existing fine-grained values, replace legacy coarse values, and
    # deduplicate every membership array. Legacy edit explicitly retains all
    # visibility granted by the previous contract.
    op.execute(
        sa.text(
            """
            WITH normalized AS (
                SELECT
                    tm.id,
                    jsonb_agg(to_jsonb(p.permission) ORDER BY p.permission)
                        AS permissions
                FROM tree_memberships AS tm
                CROSS JOIN LATERAL (
                    SELECT DISTINCT permission
                    FROM (
                        SELECT value AS permission
                        FROM jsonb_array_elements_text(tm.permissions)
                        WHERE value NOT IN ('edit', 'add_persons')

                        UNION ALL

                        SELECT unnest(
                            CASE WHEN tm.permissions ? 'edit'
                                THEN ARRAY[
                                    'person_update', 'person_delete',
                                    'marriage_update', 'marriage_delete',
                                    'marriage_divorce', 'upload_photo',
                                    'view_birth_date', 'view_marriage_date',
                                    'view_photo'
                                ]::text[]
                                ELSE ARRAY[]::text[]
                            END
                        )

                        UNION ALL

                        SELECT unnest(
                            CASE WHEN tm.permissions ? 'add_persons'
                                THEN ARRAY[
                                    'person_create', 'marriage_create'
                                ]::text[]
                                ELSE ARRAY[]::text[]
                            END
                        )
                    ) AS mapped
                ) AS p
                GROUP BY tm.id
            )
            UPDATE tree_memberships AS tm
            SET permissions = normalized.permissions
            FROM normalized
            WHERE tm.id = normalized.id
            """
        )
    )


def downgrade() -> None:
    # This is necessarily lossy: operation-level grants collapse back into the
    # two legacy capabilities. Visibility permissions remain unchanged.
    op.execute(
        sa.text(
            """
            WITH normalized AS (
                SELECT
                    tm.id,
                    jsonb_agg(to_jsonb(p.permission) ORDER BY p.permission)
                        AS permissions
                FROM tree_memberships AS tm
                CROSS JOIN LATERAL (
                    SELECT DISTINCT permission
                    FROM (
                        SELECT value AS permission
                        FROM jsonb_array_elements_text(tm.permissions)
                        WHERE value NOT IN (
                            'person_create', 'person_update', 'person_delete',
                            'marriage_create', 'marriage_update',
                            'marriage_delete', 'marriage_divorce',
                            'upload_photo', 'member_add', 'member_remove'
                        )

                        UNION ALL

                        SELECT 'edit'
                        WHERE tm.permissions ?| ARRAY[
                            'person_update', 'person_delete',
                            'marriage_update', 'marriage_delete',
                            'marriage_divorce', 'upload_photo'
                        ]

                        UNION ALL

                        SELECT 'add_persons'
                        WHERE tm.permissions ?| ARRAY[
                            'person_create', 'marriage_create'
                        ]
                    ) AS mapped
                ) AS p
                GROUP BY tm.id
            )
            UPDATE tree_memberships AS tm
            SET permissions = normalized.permissions
            FROM normalized
            WHERE tm.id = normalized.id
            """
        )
    )
