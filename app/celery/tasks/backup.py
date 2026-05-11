import datetime
import logging
import os
import subprocess  # nosec B404
from pathlib import Path

from celery import shared_task
from neo4j_backup import Extractor

from app.core.config import settings
from app.infrastructure.database.neo4j.neo4j import neo4j_client

logger = logging.getLogger(__name__)
backup_dir = Path(settings.BACKUP_DIR)


def backup_postgres():
    env = os.environ.copy()
    env["PGPASSWORD"] = settings.POSTGRES_PASSWORD
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

    os.makedirs(settings.BACKUP_DIR, exist_ok=True)

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


def backup_neo4j():
    # Create timestamped backup directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    neo_backup_dir = str(backup_dir) + f"/neo_{timestamp}"

    try:
        # Extract all data
        extractor = Extractor(
            project_dir=neo_backup_dir,
            driver=neo4j_client,
            database="neo4j",
            input_yes=True,
            compress=True,
            pull_uniqueness_constraints=True,
        )

        print(f"Starting backup neo4j to {backup_dir}...")
        extractor.extract_data()
        print(f"Backup neo4j completed successfully! Saved to: {backup_dir}")

        return backup_dir

    except Exception as e:
        logger.error(f"Unexpected error during backup Neo4j: {e}")
        raise


@shared_task(name="backup.database", bind=True, max_retries=5, retry_backoff=True)
def create_postgres_backup(self):
    backup_file = backup_postgres()
    backup_neo4j_file = backup_neo4j()
    return {
        "postgres": f"success to {backup_file}",
        "neo4j": f"success to {backup_neo4j_file}",
    }
