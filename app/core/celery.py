from celery import Celery
from celery.schedules import crontab
from app.core.config import setting
import os
import datetime
import subprocess

celery = Celery(
    "backup",
    broker=setting.CELERY_BROKER_URL,
    backend=setting.CELERY_RESULT_BACKEND,
)
celery.conf.beat_schedule = {
    "daily-postgres-backup": {
        "task": "app.task.backup",
        "schedule": crontab(hour=0, minute=0),
    }
}

celery.conf.update(
    timezone="Asia/Tehran",
    enable_utc=False,
)


def backup_postgres():
    env = os.environ.copy()
    env["PGPASSWORD"] = setting.POSTGRES_PASSWORD
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

    os.makedirs(setting.BACKUP_DIR, exist_ok=True)

    dump_file = os.path.join(setting.BACKUP_DIR, f"backup_{timestamp}.sql")
    cmd = [
        "pg_dump",
        "-U",
        setting.POSTGRES_USER,
        "-h",
        setting.POSTGRES_HOST,
        "-p",
        str(setting.POSTGRES_PORT),
        "-F",
        "c",
        "-f",
        dump_file,
        setting.POSTGRES_DB,
    ]

    try:
        subprocess.run(cmd, check=True, env=env, timeout=600)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Backup failed: {e}")
    return dump_file


@celery.task(name="app.task.backup")
def create_postgres_backup():
    backup_file = backup_postgres()
    return {"status": "success", "file": backup_file}
