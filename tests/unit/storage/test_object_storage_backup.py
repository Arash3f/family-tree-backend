from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.storage import object_storage_backup as mod


def test_dated_prefix_includes_root():
    with patch.object(mod.settings, "OFFSITE_BACKUP_PREFIX", "backups"):
        store = mod.ObjectStorageBackup(client=MagicMock())
        prefix, path = store.dated_prefix(datetime(2026, 9, 23, 0, 0, 0, tzinfo=UTC))
    assert path == "2026/2026-09/2026-09-23_00-00-00"
    assert prefix == "backups/2026/2026-09/2026-09-23_00-00-00/"


def test_upload_backup_run_uploads_three_files(tmp_path: Path):
    postgres = tmp_path / "backup_2026-09-23_00-00-00.sql"
    postgres.write_bytes(b"pg-dump")
    neo_dir = tmp_path / "neo_2026-09-23_00-00-00"
    neo_dir.mkdir()
    (neo_dir / "nodes.json").write_text("[]", encoding="utf-8")

    client = MagicMock()
    store = mod.ObjectStorageBackup(client=client)

    with (
        patch.object(mod.settings, "OFFSITE_BACKUP_BUCKET", "family-backups"),
        patch.object(mod.settings, "OFFSITE_BACKUP_PREFIX", "backups"),
        patch.object(mod.settings, "OFFSITE_BACKUP_RETENTION_DAYS", 0),
        patch.object(mod.settings, "POSTGRES_DB", "family_tree"),
    ):
        result = mod.upload_backup_run(
            timestamp="2026-09-23_00-00-00",
            postgres_dump=postgres,
            neo4j_dir=neo_dir,
            storage=store,
        )

    assert result.folder_path == "2026/2026-09/2026-09-23_00-00-00"
    assert len(result.files) == 3
    assert {item.name for item in result.files} == {
        "postgres_family_tree_2026-09-23_00-00-00.dump",
        "neo4j_2026-09-23_00-00-00.zip",
        "manifest.json",
    }
    assert client.upload_file.call_count == 3
    assert result.pruned_folders == 0


def test_prune_expired_deletes_old_run_prefix():
    client = MagicMock()
    client.get_paginator.return_value.paginate.return_value = [
        {
            "Contents": [
                {
                    "Key": "backups/2026/2026-01/2026-01-01_00-00-00/postgres.dump",
                },
                {
                    "Key": "backups/2026/2026-09/2026-09-23_00-00-00/postgres.dump",
                },
            ]
        }
    ]
    store = mod.ObjectStorageBackup(client=client)

    with (
        patch.object(mod.settings, "OFFSITE_BACKUP_BUCKET", "family-backups"),
        patch.object(mod.settings, "OFFSITE_BACKUP_PREFIX", "backups"),
    ):
        removed = store.prune_expired(cutoff=datetime(2026, 6, 1, tzinfo=UTC))

    assert removed == 1
    client.delete_objects.assert_called()


def test_create_postgres_backup_queues_offsite(tmp_path: Path):
    from app.celery.tasks import backup as backup_module

    with (
        patch.object(backup_module, "backup_postgres", return_value="pg.sql"),
        patch.object(backup_module, "backup_neo4j", return_value=str(tmp_path)),
        patch.object(backup_module.settings, "OFFSITE_BACKUP_ENABLED", True),
        patch.object(backup_module.upload_backup_offsite, "delay") as delay,
    ):
        result = backup_module.create_postgres_backup.run()

    assert result["offsite"] == "queued"
    delay.assert_called_once()


def test_offsite_validator_rejects_half_config():
    from pydantic import ValidationError

    from app.core.config import AppSettings

    with pytest.raises(ValidationError, match="OFFSITE_BACKUP_ENABLED is true"):
        AppSettings(
            _env_file=None,  # type: ignore[call-arg]
            JWT_SECRET="local-dev-only-change-me-32chars-min",
            POSTGRES_HOST="127.0.0.1",
            POSTGRES_PORT=5432,
            POSTGRES_DB="family_tree",
            POSTGRES_HOST_TEST="127.0.0.1",
            POSTGRES_PORT_TEST=5432,
            POSTGRES_DB_TEST="family_tree_test",
            OFFSITE_BACKUP_ENABLED=True,
            OFFSITE_BACKUP_ENDPOINT="s3.ir-thr-at1.arvanstorage.ir",
        )
