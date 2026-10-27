"""Allow the upgrade_request ticket category.

Revision ID: 0025_ticket_upgrade_request
Revises: 0024_user_paid_until
Create Date: 2026-10-27 09:05:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0025_ticket_upgrade_request"
down_revision: Union[str, Sequence[str], None] = "0024_user_paid_until"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BEFORE = ("general", "account", "technical", "bug", "feature_request", "other")
_AFTER = (*_BEFORE, "upgrade_request")


def _replace_check(categories: tuple[str, ...]) -> None:
    op.drop_constraint("ck_ticket_category", "tickets", type_="check")
    op.create_check_constraint(
        "ck_ticket_category",
        "tickets",
        "category IN (" + ", ".join(f"'{c}'" for c in categories) + ")",
    )


def upgrade() -> None:
    _replace_check(_AFTER)


def downgrade() -> None:
    # An upgrade request has no older category that means the same thing;
    # "account" is the closest, so keep the ticket rather than drop it.
    op.execute(
        "UPDATE tickets SET category = 'account' WHERE category = 'upgrade_request'"
    )
    _replace_check(_BEFORE)
