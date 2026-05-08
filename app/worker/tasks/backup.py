import os
import datetime
import subprocess

from celery import shared_task
from app.core.config import setting


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


@shared_task(name="backup.database", bind=True, max_retries=5, retry_backoff=True)
def create_postgres_backup():
    backup_file = backup_postgres()
    return {"status": "success", "file": backup_file}
