import logging

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_failure

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "family_tree_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tehran",
    enable_utc=True,
    task_routes={
        "backup.database": {"queue": "backup_database"},
        "sync.person.*": {"queue": "sync_person"},
        "sync.relationship.*": {"queue": "sync_relationship"},
        "reconcile.neo4j": {"queue": "reconcile_neo4j"},
    },
)

celery_app.conf.beat_schedule = {
    "daily-postgres-backup": {
        "task": "backup.database",
        "schedule": crontab(hour=0, minute=0),
    },
    "hourly-neo4j-reconciliation": {
        "task": "reconcile.neo4j",
        "schedule": crontab(minute=30),
    },
}

celery_app.autodiscover_tasks(["app.celery"])


@task_failure.connect
def _log_exhausted_task_failure(
    sender=None, task_id=None, exception=None, args=None, kwargs=None, **_extra
):
    """Loudly flag tasks that exhausted all retries.

    Sync/reconcile task failures leave Postgres and Neo4j permanently
    out of sync until the next reconciliation run — this is the only
    signal an operator has that a specific entity needs attention
    (see M9 in REVIEW.md; a real DLQ/alerting pipeline is future work).
    """
    task_name = getattr(sender, "name", "unknown")
    if not (task_name.startswith("sync.") or task_name == "reconcile.neo4j"):
        return
    logger.critical(
        "Task %s (id=%s) exhausted retries and failed permanently. "
        "args=%s kwargs=%s exception=%s",
        task_name,
        task_id,
        args,
        kwargs,
        exception,
    )
