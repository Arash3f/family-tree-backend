from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

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
    enable_utc=False,
    task_routes={
        "backup.database": {"queue": "backup_database"},
        "sync.person.*": {"queue": "sync_person"},
        "sync.relationship.*": {"queue": "sync_relationship"},
    },
)

celery_app.conf.beat_schedule = {
    "daily-postgres-backup": {
        "task": "backup.database",
        "schedule": crontab(hour=0, minute=0),
    }
}

celery_app.autodiscover_tasks(["app.worker"])
