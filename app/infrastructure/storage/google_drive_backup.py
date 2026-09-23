"""Off-site copy of the nightly dumps in Google Drive.

The nightly task writes both dumps to `BACKUP_DIR`, which is a Docker volume on
the same host as the databases — a disk or host loss takes the backups with it.
This module pushes the same files to Google Drive under a dated folder tree so
an operator can find "the backup of 2026-09-23" without reading a log.

Layout, relative to `GOOGLE_DRIVE_FOLDER_ID`:

    2026/
      2026-09/
        2026-09-23_00-00-00/
          postgres_family_tree_2026-09-23_00-00-00.dump
          neo4j_2026-09-23_00-00-00.zip
          manifest.json

Authentication is a **service account**: it has its own identity, no interactive
consent and no refresh token to expire, which is what an unattended nightly job
needs. The operator shares the destination folder with that account's email —
see the Google Drive section of `docker/README.md` for the one-time setup.

The Google client libraries are imported lazily so the whole feature stays
optional: with `GOOGLE_DRIVE_BACKUP_ENABLED=false` (the default) the packages
need not be installed at all, and nothing here is imported at boot.
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_FOLDER_MIME = "application/vnd.google-apps.folder"

# Full `drive` scope rather than `drive.file`: pruning has to delete dated
# folders that earlier deploys created, which `drive.file` (files this client
# created) cannot be relied on to cover across credential rotations.
_SCOPES = ("https://www.googleapis.com/auth/drive",)

# Google rejects a bare `'` inside a query literal; names here are timestamps
# and fixed prefixes, but escaping keeps a hand-set folder name from breaking
# the listing query.
_QUOTE_ESCAPES = str.maketrans({"\\": "\\\\", "'": "\\'"})

# Name of the dated folder, and the format `prune_expired` parses back out of
# it. Sorts chronologically as plain text, which is how Drive's UI orders it.
FOLDER_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"


class GoogleDriveBackupError(RuntimeError):
    """Raised when the off-site copy could not be completed."""


@dataclass(frozen=True)
class DriveUpload:
    """One file as it now exists in Drive."""

    name: str
    file_id: str
    size_bytes: int


@dataclass(frozen=True)
class DriveBackupResult:
    folder_path: str
    folder_id: str
    files: list[DriveUpload]
    pruned_folders: int


def _escape(value: str) -> str:
    return value.translate(_QUOTE_ESCAPES)


class GoogleDriveBackupStorage:
    """Uploads dump files into a dated folder tree and prunes expired ones.

    One instance per task run: the folder-id cache it keeps is only valid for
    as long as nobody moves folders around in the Drive UI.
    """

    def __init__(self) -> None:
        self._service: Any | None = None
        # (parent_id, name) -> folder id, so a three-level path costs three
        # lookups on the first upload of a run and none afterwards.
        self._folder_ids: dict[tuple[str, str], str] = {}

    # ── plumbing ──────────────────────────────────────────────────────────────

    @property
    def _drive(self) -> Any:
        if self._service is None:
            self._service = self._build_service()
        return self._service

    def _build_service(self) -> Any:
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError as exc:  # pragma: no cover - depends on extras
            raise GoogleDriveBackupError(
                "GOOGLE_DRIVE_BACKUP_ENABLED is on but the Google client "
                "libraries are missing. Install google-api-python-client and "
                "google-auth."
            ) from exc

        credentials_file = Path(settings.GOOGLE_DRIVE_CREDENTIALS_FILE)
        if not credentials_file.is_file():
            raise GoogleDriveBackupError(
                f"Service-account key not found at {credentials_file}. "
                "Set GOOGLE_DRIVE_CREDENTIALS_FILE to the mounted JSON key."
            )

        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_file), scopes=list(_SCOPES)
        )
        # cache_discovery=False: the default file cache warns on every call
        # under a non-writable working directory, which the runtime image is.
        return build("drive", "v3", credentials=credentials, cache_discovery=False)

    def _shared_drive_args(self) -> dict[str, Any]:
        """Extra query args a Shared Drive needs; empty for a plain My Drive folder."""
        drive_id = settings.GOOGLE_DRIVE_SHARED_DRIVE_ID.strip()
        if not drive_id:
            return {"supportsAllDrives": True}
        return {
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True,
            "corpora": "drive",
            "driveId": drive_id,
        }

    # ── folders ───────────────────────────────────────────────────────────────

    def _find_child(
        self, *, name: str, parent_id: str, folders_only: bool
    ) -> str | None:
        query = (
            f"name = '{_escape(name)}' and '{_escape(parent_id)}' in parents "
            "and trashed = false"
        )
        if folders_only:
            query += f" and mimeType = '{_FOLDER_MIME}'"

        response = (
            self._drive.files()
            .list(
                q=query,
                fields="files(id, name)",
                pageSize=1,
                **self._shared_drive_args(),
            )
            .execute()
        )
        files = response.get("files", [])
        return files[0]["id"] if files else None

    def _ensure_folder(self, *, name: str, parent_id: str) -> str:
        cached = self._folder_ids.get((parent_id, name))
        if cached is not None:
            return cached

        folder_id = self._find_child(name=name, parent_id=parent_id, folders_only=True)
        if folder_id is None:
            created = (
                self._drive.files()
                .create(
                    body={
                        "name": name,
                        "mimeType": _FOLDER_MIME,
                        "parents": [parent_id],
                    },
                    fields="id",
                    supportsAllDrives=True,
                )
                .execute()
            )
            folder_id = created["id"]

        self._folder_ids[(parent_id, name)] = folder_id
        return folder_id

    def ensure_dated_folder(self, moment: datetime) -> tuple[str, str]:
        """Create (or reuse) `YYYY/YYYY-MM/YYYY-MM-DD_HH-MM-SS` under the root.

        @param moment - The nominal instant of the backup run.

        @returns A `(folder_id, human_readable_path)` pair.

        @throws {GoogleDriveBackupError} When the root folder is unset.
        """
        root_id = settings.GOOGLE_DRIVE_FOLDER_ID.strip()
        if not root_id:
            raise GoogleDriveBackupError(
                "GOOGLE_DRIVE_FOLDER_ID is empty; share a Drive folder with the "
                "service account and set its id."
            )

        parts = (
            moment.strftime("%Y"),
            moment.strftime("%Y-%m"),
            moment.strftime(FOLDER_TIMESTAMP_FORMAT),
        )
        parent_id = root_id
        for part in parts:
            parent_id = self._ensure_folder(name=part, parent_id=parent_id)
        return parent_id, "/".join(parts)

    # ── files ─────────────────────────────────────────────────────────────────

    def upload_file(self, source: Path, *, folder_id: str) -> DriveUpload:
        """Upload one file, replacing a same-named file in that folder.

        @param source - Local file to copy up.
        @param folder_id - Destination folder id.

        @returns The uploaded file's name, Drive id and size.

        @throws {GoogleDriveBackupError} When the local file is missing.
        """
        from googleapiclient.http import MediaFileUpload

        if not source.is_file():
            raise GoogleDriveBackupError(f"Nothing to upload at {source}")

        # Resumable: a multi-hundred-MB dump over a flaky link should retry the
        # failed chunk rather than the whole transfer.
        media = MediaFileUpload(str(source), resumable=True)
        existing_id = self._find_child(
            name=source.name, parent_id=folder_id, folders_only=False
        )

        if existing_id is None:
            uploaded = (
                self._drive.files()
                .create(
                    body={"name": source.name, "parents": [folder_id]},
                    media_body=media,
                    fields="id, name, size",
                    supportsAllDrives=True,
                )
                .execute()
            )
        else:
            # A retried task must not leave two copies of the same dump behind.
            uploaded = (
                self._drive.files()
                .update(
                    fileId=existing_id,
                    media_body=media,
                    fields="id, name, size",
                    supportsAllDrives=True,
                )
                .execute()
            )

        return DriveUpload(
            name=uploaded["name"],
            file_id=uploaded["id"],
            size_bytes=int(uploaded.get("size") or source.stat().st_size),
        )

    # ── retention ─────────────────────────────────────────────────────────────

    def prune_expired(self, *, cutoff: datetime) -> int:
        """Trash dated folders whose name is older than `cutoff`."""
        root_id = settings.GOOGLE_DRIVE_FOLDER_ID.strip()
        removed = 0

        for year_id in self._child_folder_ids(root_id):
            for month_id in self._child_folder_ids(year_id):
                for folder_id, name in self._child_folders(month_id):
                    try:
                        moment = datetime.strptime(name, FOLDER_TIMESTAMP_FORMAT)
                    except ValueError:
                        # A folder someone added by hand is not ours to delete.
                        continue
                    if moment.replace(tzinfo=UTC) >= cutoff:
                        continue
                    self._drive.files().delete(
                        fileId=folder_id, supportsAllDrives=True
                    ).execute()
                    removed += 1
                    logger.info("Pruned expired Drive backup folder %s", name)

        return removed

    def _child_folders(self, parent_id: str) -> list[tuple[str, str]]:
        query = (
            f"'{_escape(parent_id)}' in parents and trashed = false "
            f"and mimeType = '{_FOLDER_MIME}'"
        )
        folders: list[tuple[str, str]] = []
        page_token: str | None = None
        while True:
            response = (
                self._drive.files()
                .list(
                    q=query,
                    fields="nextPageToken, files(id, name)",
                    pageSize=200,
                    pageToken=page_token,
                    **self._shared_drive_args(),
                )
                .execute()
            )
            folders.extend(
                (item["id"], item["name"]) for item in response.get("files", [])
            )
            page_token = response.get("nextPageToken")
            if not page_token:
                return folders

    def _child_folder_ids(self, parent_id: str) -> list[str]:
        return [folder_id for folder_id, _ in self._child_folders(parent_id)]


def archive_directory(source: Path) -> Path:
    """Zip a directory next to itself so it can travel as a single file.

    The Neo4j extractor writes a directory; Drive holds files. Zipping keeps one
    restorable artefact per store per run instead of a folder of loose parts.

    @param source - Directory to compress.

    @returns Path of the written `.zip`.

    @throws {GoogleDriveBackupError} When `source` is not a directory.
    """
    if not source.is_dir():
        raise GoogleDriveBackupError(f"Not a directory: {source}")
    archive = shutil.make_archive(str(source), "zip", root_dir=str(source))
    return Path(archive)


def _write_manifest(
    folder: Path, *, timestamp: str, uploads: list[DriveUpload]
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
                    {"name": item.name, "size_bytes": item.size_bytes}
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
) -> DriveBackupResult:
    """Copy one nightly run to Drive and prune runs past the retention window.

    @param timestamp - The run's `%Y-%m-%d_%H-%M-%S` stamp, reused as the folder name.
    @param postgres_dump - The `pg_dump` custom-format file.
    @param neo4j_dir - Directory the Neo4j extractor wrote.

    @returns Where the run landed and how many expired folders were removed.
    - `folder_path` - Human-readable `YYYY/YYYY-MM/<timestamp>` path.
    - `files` - Every file now present in that folder.
    - `pruned_folders` - Count of expired folders trashed in the same pass.

    @throws {GoogleDriveBackupError} When credentials, the root folder id or a
        source file is missing, or the Google client libraries are not installed.

    @example
    ```python
    upload_backup_run(
        timestamp="2026-09-23_00-00-00",
        postgres_dump=Path("/mnt/backups/backup_2026-09-23_00-00-00.sql"),
        neo4j_dir=Path("/mnt/backups/neo_2026-09-23_00-00-00"),
    )
    ```
    """
    moment = datetime.strptime(timestamp, FOLDER_TIMESTAMP_FORMAT).replace(tzinfo=UTC)
    storage = GoogleDriveBackupStorage()
    folder_id, folder_path = storage.ensure_dated_folder(moment)

    # Named for what they are once they leave the machine that made them: the
    # local file names are positional, the remote ones have to stand alone.
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
        storage.upload_file(postgres_target, folder_id=folder_id),
        storage.upload_file(neo4j_target, folder_id=folder_id),
    ]
    manifest = _write_manifest(
        postgres_target.parent, timestamp=timestamp, uploads=uploads
    )
    uploads.append(storage.upload_file(manifest, folder_id=folder_id))

    retention_days = settings.GOOGLE_DRIVE_RETENTION_DAYS
    pruned = 0
    if retention_days > 0:
        pruned = storage.prune_expired(
            cutoff=datetime.now(UTC) - timedelta(days=retention_days)
        )

    logger.info(
        "Uploaded backup %s to Drive folder %s (%s file(s), %s expired folder(s))",
        timestamp,
        folder_path,
        len(uploads),
        pruned,
    )
    return DriveBackupResult(
        folder_path=folder_path,
        folder_id=folder_id,
        files=uploads,
        pruned_folders=pruned,
    )
