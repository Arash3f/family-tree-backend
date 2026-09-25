"""Off-site copy of the nightly dumps to S3-compatible object storage.

The nightly task writes both dumps to `BACKUP_DIR`, which is a Docker volume on
the same host as the databases — a disk or host loss takes the backups with it.
This module pushes the same files to an S3-compatible bucket (intended target:
Arvan Cloud Object Storage / گنجینه) under a dated key tree so an operator can
find "the backup of 2026-09-23" without reading a log.

Layout, relative to `OFFSITE_BACKUP_PREFIX` inside `OFFSITE_BACKUP_BUCKET`:

    2026/
      2026-09/
        2026-09-23_00-00-00/
          postgres_family_tree_2026-09-23_00-00-00.dump
          neo4j_2026-09-23_00-00-00.zip
          manifest.json

Separate from the MinIO settings used for photos/media. Credentials are Access
Key + Secret Key from the provider panel — see `OFFSITE-BACKUP.md`.
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

FOLDER_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"


class OffsiteBackupError(RuntimeError):
    """Raised when the off-site copy could not be completed."""


@dataclass(frozen=True)
class OffsiteUpload:
    """One object as it now exists in the bucket."""

    name: str
    key: str
    size_bytes: int


@dataclass(frozen=True)
class OffsiteBackupResult:
    folder_path: str
    prefix: str
    files: list[OffsiteUpload]
    pruned_folders: int


class ObjectStorageBackup:
    """Uploads dump files under a dated key prefix and prunes expired runs."""

    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> Any:
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - shipped via aioboto3
            raise OffsiteBackupError(
                "OFFSITE_BACKUP_ENABLED is on but boto3 is missing."
            ) from exc

        endpoint = settings.OFFSITE_BACKUP_ENDPOINT.strip()
        if not endpoint:
            raise OffsiteBackupError("OFFSITE_BACKUP_ENDPOINT is empty.")

        scheme = "https" if settings.OFFSITE_BACKUP_SECURE else "http"
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            endpoint_url = endpoint
        else:
            endpoint_url = f"{scheme}://{endpoint}"

        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.OFFSITE_BACKUP_ACCESS_KEY,
            aws_secret_access_key=settings.OFFSITE_BACKUP_SECRET_KEY,
            region_name=settings.OFFSITE_BACKUP_REGION,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def _bucket(self) -> str:
        bucket = settings.OFFSITE_BACKUP_BUCKET.strip()
        if not bucket:
            raise OffsiteBackupError("OFFSITE_BACKUP_BUCKET is empty.")
        return bucket

    def _root_prefix(self) -> str:
        return settings.OFFSITE_BACKUP_PREFIX.strip().strip("/")

    def dated_prefix(self, moment: datetime) -> tuple[str, str]:
        """Build `YYYY/YYYY-MM/YYYY-MM-DD_HH-MM-SS` under the configured root.

        @returns `(full_prefix_with_trailing_slash, human_readable_path)`.
        """
        parts = (
            moment.strftime("%Y"),
            moment.strftime("%Y-%m"),
            moment.strftime(FOLDER_TIMESTAMP_FORMAT),
        )
        relative = "/".join(parts)
        root = self._root_prefix()
        full = f"{root}/{relative}" if root else relative
        return f"{full}/", relative

    def upload_file(self, source: Path, *, prefix: str) -> OffsiteUpload:
        if not source.is_file():
            raise OffsiteBackupError(f"Nothing to upload at {source}")

        key = f"{prefix.rstrip('/')}/{source.name}"
        size = source.stat().st_size
        try:
            self.client.upload_file(
                Filename=str(source),
                Bucket=self._bucket(),
                Key=key,
            )
        except (ClientError, BotoCoreError, OSError) as exc:
            raise OffsiteBackupError(f"Upload failed for {key}: {exc}") from exc

        return OffsiteUpload(name=source.name, key=key, size_bytes=size)

    def prune_expired(self, *, cutoff: datetime) -> int:
        """Delete object trees whose run folder name is older than `cutoff`."""
        root = self._root_prefix()
        list_prefix = f"{root}/" if root else ""
        bucket = self._bucket()
        run_prefixes: set[str] = set()

        try:
            paginator = self.client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket, Prefix=list_prefix):
                for item in page.get("Contents") or []:
                    key = item["Key"]
                    relative = key[len(list_prefix) :] if list_prefix else key
                    parts = relative.split("/")
                    if len(parts) < 3:
                        continue
                    year, month, run = parts[0], parts[1], parts[2]
                    try:
                        moment = datetime.strptime(run, FOLDER_TIMESTAMP_FORMAT)
                    except ValueError:
                        continue
                    if moment.replace(tzinfo=UTC) >= cutoff:
                        continue
                    run_prefix = (
                        f"{list_prefix}{year}/{month}/{run}/"
                        if list_prefix
                        else f"{year}/{month}/{run}/"
                    )
                    run_prefixes.add(run_prefix)
        except (ClientError, BotoCoreError) as exc:
            raise OffsiteBackupError(
                f"Failed to list backups for prune: {exc}"
            ) from exc

        removed = 0
        for run_prefix in sorted(run_prefixes):
            self._delete_prefix(run_prefix)
            removed += 1
            logger.info("Pruned expired off-site backup prefix %s", run_prefix)

        return removed

    def _delete_prefix(self, prefix: str) -> None:
        bucket = self._bucket()
        paginator = self.client.get_paginator("list_objects_v2")
        to_delete: list[dict[str, str]] = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for item in page.get("Contents") or []:
                to_delete.append({"Key": item["Key"]})
                if len(to_delete) >= 1000:
                    self.client.delete_objects(
                        Bucket=bucket, Delete={"Objects": to_delete}
                    )
                    to_delete = []
        if to_delete:
            self.client.delete_objects(Bucket=bucket, Delete={"Objects": to_delete})


def archive_directory(source: Path) -> Path:
    """Zip a directory next to itself so it can travel as a single object."""
    if not source.is_dir():
        raise OffsiteBackupError(f"Not a directory: {source}")
    archive = shutil.make_archive(str(source), "zip", root_dir=str(source))
    return Path(archive)


def _write_manifest(
    folder: Path, *, timestamp: str, uploads: list[OffsiteUpload]
) -> Path:
    """Record what the run produced, so a restore does not depend on log history."""
    manifest = folder / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "timestamp": timestamp,
                "created_at": datetime.now(UTC).isoformat(),
                "postgres_database": settings.POSTGRES_DB,
                "environment": settings.normalized_environment,
                "files": [
                    {
                        "name": item.name,
                        "key": item.key,
                        "size_bytes": item.size_bytes,
                    }
                    for item in uploads
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest


def upload_backup_run(
    *,
    timestamp: str,
    postgres_dump: Path,
    neo4j_dir: Path,
    storage: ObjectStorageBackup | None = None,
) -> OffsiteBackupResult:
    """Copy one nightly run to object storage and prune runs past retention.

    @param timestamp - The run's `%Y-%m-%d_%H-%M-%S` stamp, reused as the folder name.
    @param postgres_dump - The `pg_dump` custom-format file.
    @param neo4j_dir - Directory the Neo4j extractor wrote.
    @param storage - Optional pre-built client wrapper (tests inject a mock).
    """
    moment = datetime.strptime(timestamp, FOLDER_TIMESTAMP_FORMAT).replace(tzinfo=UTC)
    store = storage or ObjectStorageBackup()
    prefix, folder_path = store.dated_prefix(moment)

    postgres_target = postgres_dump.with_name(
        f"postgres_{settings.POSTGRES_DB}_{timestamp}.dump"
    )
    if postgres_target != postgres_dump:
        shutil.copy2(postgres_dump, postgres_target)

    neo4j_archive = archive_directory(neo4j_dir)
    neo4j_target = neo4j_archive.with_name(f"neo4j_{timestamp}.zip")
    if neo4j_target != neo4j_archive:
        neo4j_archive.replace(neo4j_target)

    uploads = [
        store.upload_file(postgres_target, prefix=prefix),
        store.upload_file(neo4j_target, prefix=prefix),
    ]
    manifest = _write_manifest(
        postgres_target.parent, timestamp=timestamp, uploads=uploads
    )
    uploads.append(store.upload_file(manifest, prefix=prefix))

    retention_days = settings.OFFSITE_BACKUP_RETENTION_DAYS
    pruned = 0
    if retention_days > 0:
        pruned = store.prune_expired(
            cutoff=datetime.now(UTC) - timedelta(days=retention_days)
        )

    logger.info(
        "Uploaded backup %s to off-site prefix %s (%s file(s), %s expired run(s))",
        timestamp,
        folder_path,
        len(uploads),
        pruned,
    )
    return OffsiteBackupResult(
        folder_path=folder_path,
        prefix=prefix,
        files=uploads,
        pruned_folders=pruned,
    )
