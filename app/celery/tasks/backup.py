import datetime
import logging
import os
import subprocess  # nosec B404
from pathlib import Path

from celery import shared_task
from neo4j import GraphDatabase
from neo4j_backup import Extractor

from app.core.config import settings
from app.infrastructure.storage.google_drive_backup import (
    GoogleDriveBackupError,
    upload_backup_run,
)

logger = logging.getLogger(__name__)
backup_dir = Path(settings.BACKUP_DIR)


def backup_postgres(timestamp: str):
    env = os.environ.copy()
    env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

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
    except OSError as e:
        logger.error(f"Unexpected error during backup: {e}")
        raise


def backup_neo4j(timestamp: str):
    # Reuses the Postgres backup's timestamp so both dumps carry the same
    # nominal instant, keeping restores as close to consistent as two
    # independently-snapshotted databases can get (see M4 in REVIEW.md — a
    # real point-in-time-consistent snapshot would need write-pausing or WAL
    # coordination across both stores).
    neo_backup_dir = str(backup_dir) + f"/neo_{timestamp}"

    # neo4j_backup's Extractor only supports the SYNC driver API, so we open
    # a small dedicated sync driver here rather than reusing the app's
    # request-path `neo4j_client` (which now wraps an ASYNC driver since the
    # sync-to-async Neo4j migration). This keeps backup/restore fully
    # decoupled from the async request-path driver.
    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        max_connection_lifetime=1000,
        connection_timeout=5,
    )

    try:
        # Extract all data
        extractor = Extractor(
            project_dir=neo_backup_dir,
            driver=driver,
            database="neo4j",
            input_yes=True,
            compress=True,
            pull_uniqueness_constraints=True,
        )

        logger.info(f"Starting backup neo4j to {neo_backup_dir}...")
        extractor.extract_data()
        logger.info(f"Backup neo4j completed successfully! Saved to: {neo_backup_dir}")

        return neo_backup_dir

    except (OSError, RuntimeError) as e:
        logger.error(f"Unexpected error during backup Neo4j: {e}")
        raise
    finally:
        driver.close()


@shared_task(name="backup.database", bind=True, max_retries=5, retry_backoff=True)
def create_postgres_backup(self):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = backup_postgres(timestamp)
    backup_neo4j_file = backup_neo4j(timestamp)

    # Handing the upload to its own task keeps the two failure modes apart: a
    # Drive outage retries the transfer on its own schedule instead of running
    # pg_dump against the live database five more times.
    if settings.GOOGLE_DRIVE_BACKUP_ENABLED:
        upload_backup_to_drive.delay(
            timestamp=timestamp,
            postgres_dump=backup_file,
            neo4j_dir=backup_neo4j_file,
        )

    return {
        "postgres": f"success to {backup_file}",
        "neo4j": f"success to {backup_neo4j_file}",
        "google_drive": "queued" if settings.GOOGLE_DRIVE_BACKUP_ENABLED else "off",
    }


@shared_task(
    name="backup.upload_to_drive", bind=True, max_retries=5, retry_backoff=True
)
def upload_backup_to_drive(self, *, timestamp: str, postgres_dump: str, neo4j_dir: str):
    """Copy one finished backup run to Google Drive and prune expired runs.

    @param timestamp - The run stamp, reused as the dated folder name.
    @param postgres_dump - Path of the pg_dump file on the worker.
    @param neo4j_dir - Path of the directory the Neo4j extractor wrote.

    @returns The Drive folder the run landed in and how many files were sent.

    @throws {GoogleDriveBackupError} Retried; raised for good once the retries
        run out, leaving the local copies untouched.
    """
    try:
        result = upload_backup_run(
            timestamp=timestamp,
            postgres_dump=Path(postgres_dump),
            neo4j_dir=Path(neo4j_dir),
        )
    except (GoogleDriveBackupError, OSError) as exc:
        # The local dumps are already on disk, so a failed upload costs the
        # off-site copy only — never the backup itself.
        logger.error("Google Drive upload failed for %s: %s", timestamp, exc)
        raise self.retry(exc=exc) from exc

    return {
        "folder": result.folder_path,
        "files": [item.name for item in result.files],
        "pruned_folders": result.pruned_folders,
    }
