import datetime
import logging
import os
import subprocess  # nosec B404
from pathlib import Path

from celery import shared_task

from app.core.config import settings

logger = logging.getLogger(__name__)


def backup_postgres():
    env = os.environ.copy()
    env["PGPASSWORD"] = settings.POSTGRES_PASSWORD
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

    os.makedirs(settings.BACKUP_DIR, exist_ok=True)

    backup_dir = Path(settings.BACKUP_DIR)
    dump_file = backup_dir / f"backup_{timestamp}.sql"

    cmd = [
        "pg_dump",
        "-U",
        str(settings.POSTGRES_USER),
        "-h",
        str(settings.POSTGRES_HOST),
        "-p",
        str(settings.POSTGRES_PORT),
        "-F",
        "c",
        "-f",
        str(dump_file),
        str(settings.POSTGRES_DB),
    ]

    logger.info(f"Starting backup to {dump_file}")

    try:
        subprocess.run(
            cmd, check=True, env=env, timeout=600, capture_output=True, text=True
        )  # nosec B603
        logger.info(f"Backup completed successfully: {dump_file}")

        return str(dump_file)

    except subprocess.TimeoutExpired:
        logger.error("Backup timeout after 600 seconds")
        raise RuntimeError("Backup timeout")
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed with exit code {e.returncode}: {e.stderr}")
        raise RuntimeError(f"Backup failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error during backup: {e}")
        raise


@shared_task(name="backup.database", bind=True, max_retries=5, retry_backoff=True)
def create_postgres_backup():
    backup_file = backup_postgres()
    return {"status": "success", "file": backup_file}
