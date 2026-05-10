import datetime
import os
import subprocess

from celery import shared_task

from app.core.config import settings


def backup_postgres():
    env = os.environ.copy()
    env["PGPASSWORD"] = settings.POSTGRES_PASSWORD
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

    os.makedirs(settings.BACKUP_DIR, exist_ok=True)

    dump_file = os.path.join(settings.BACKUP_DIR, f"backup_{timestamp}.sql")
    cmd = [
        "pg_dump",
        "-U",
        settings.POSTGRES_USER,
        "-h",
        settings.POSTGRES_HOST,
        "-p",
        str(settings.POSTGRES_PORT),
        "-F",
        "c",
        "-f",
        dump_file,
        settings.POSTGRES_DB,
    ]

    try:
        subprocess.run(cmd, check=True, env=env, timeout=600)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Backup failed: {e}")
    return dump_file


@shared_task(name="backup.database", bind=True, max_retries=5, retry_backoff=True)
def create_postgres_backup():
    backup_file = backup_postgres()
    return {"status": "success", "file": backup_file}
