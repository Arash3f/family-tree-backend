import logging
from datetime import UTC, datetime

from celery import shared_task

from app.infrastructure.database.neo4j.neo4j import run_celery_coro
from app.infrastructure.database.session import async_session
from app.infrastructure.repositories.user_repository_sql import SQLUserRepository

logger = logging.getLogger(__name__)


async def _downgrade_lapsed() -> int:
    async with async_session() as session:
        downgraded = await SQLUserRepository(session).downgrade_lapsed_paid_plans(
            datetime.now(UTC).date()
        )
        await session.commit()
        return downgraded


@shared_task(
    name="accounts.expire_paid_plans",
    bind=True,
    max_retries=3,
    retry_backoff=True,
    autoretry_for=(ConnectionError, TimeoutError),
)
def expire_paid_plans(self) -> int:
    """Store paid plans whose last day has passed as free.

    Quotas already apply from the day after `paid_until` (see
    `effective_account_type`); this keeps the stored plan, the admin user list
    and its sorting in step with that. Nothing is deleted: a lapsed account
    keeps every tree and person, it only stops being able to add past the
    free quotas.

    @returns How many accounts were downgraded.
    """
    downgraded = run_celery_coro(_downgrade_lapsed())
    logger.info("Paid plan expiry: %d account(s) moved to free", downgraded)
    return downgraded
