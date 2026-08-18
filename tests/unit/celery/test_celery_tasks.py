from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
import redis
from celery.exceptions import Retry

from app.celery.tasks import backup as backup_module
from app.celery.tasks import reconcile_neo4j as reconcile_module
from app.celery.tasks import sync_person as sync_person_module
from app.celery.tasks import sync_relationships as sync_rel_module


def test_sync_person_upsert_success():
    payload = {
        "id": str(UUID(int=1)),
        "tree_id": str(UUID(int=99)),
        "full_name": "Ali",
        "gender": "MALE",
        "birth_date": None,
        "death_date": None,
    }
    with patch.object(sync_person_module, "repo", new=AsyncMock()) as repo:
        sync_person_module.sync_person_upsert.run(payload)
        repo.upsert_person.assert_called_once()


def test_sync_person_upsert_retries_on_error():
    payload = {
        "id": str(UUID(int=1)),
        "tree_id": str(UUID(int=99)),
        "full_name": "Ali",
        "gender": "MALE",
        "birth_date": None,
        "death_date": None,
    }
    with patch.object(sync_person_module, "repo", new=AsyncMock()) as repo:
        repo.upsert_person.side_effect = RuntimeError("fail")
        with (
            patch.object(
                sync_person_module.sync_person_upsert,
                "retry",
                side_effect=Retry(),
            ),
            pytest.raises(Retry),
        ):
            sync_person_module.sync_person_upsert.run(payload)


def test_sync_person_delete_success():
    with patch.object(sync_person_module, "repo", new=AsyncMock()) as repo:
        sync_person_module.sync_person_delete.run(str(UUID(int=1)))
        repo.delete_person.assert_called_once()


def test_sync_relationship_tasks():
    pid1, pid2 = str(UUID(int=1)), str(UUID(int=2))
    with patch.object(sync_rel_module, "repo", new=AsyncMock()) as repo:
        sync_rel_module.sync_parent_relationship.run(pid1, pid2)
        sync_rel_module.sync_parent_rel_delete.run(pid1, pid2)
        sync_rel_module.sync_spouse_relationship.run(pid1, pid2)
        sync_rel_module.sync_spouse_relationship_delete.run(pid1, pid2)
        assert repo.create_parent_relationship.call_count == 1
        assert repo.delete_parent_relationship.call_count == 1
        assert repo.create_spouse_relationship.call_count == 1
        assert repo.delete_spouse_relationship.call_count == 1


def test_backup_postgres_success(tmp_path):
    with (
        patch.object(backup_module.settings, "BACKUP_DIR", str(tmp_path)),
        patch.object(backup_module, "backup_dir", tmp_path),
        patch("app.celery.tasks.backup.subprocess.run") as run,
    ):
        run.return_value = MagicMock()
        path = backup_module.backup_postgres("2026-01-01_00-00-00")
        assert path.endswith(".sql")
        run.assert_called_once()


def test_backup_postgres_timeout(tmp_path):
    import subprocess

    with (
        patch.object(backup_module.settings, "BACKUP_DIR", str(tmp_path)),
        patch.object(backup_module, "backup_dir", tmp_path),
        patch(
            "app.celery.tasks.backup.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="pg_dump", timeout=1),
        ),
        pytest.raises(RuntimeError, match="Backup timeout"),
    ):
        backup_module.backup_postgres("2026-01-01_00-00-00")


def test_backup_neo4j_success(tmp_path):
    # backup_neo4j() now opens its own local sync GraphDatabase driver
    # (decoupled from the app's async `neo4j_client`) since neo4j_backup's
    # Extractor only supports the sync driver API. Patch that constructor
    # instead of `neo4j_client._driver`.
    with (
        patch.object(backup_module, "backup_dir", tmp_path),
        patch("app.celery.tasks.backup.Extractor") as extractor_cls,
        patch("app.celery.tasks.backup.GraphDatabase") as graph_database_cls,
    ):
        graph_database_cls.driver.return_value = MagicMock()
        result = backup_module.backup_neo4j("2026-01-01_00-00-00")
        extractor_cls.return_value.extract_data.assert_called_once()
        assert result == str(tmp_path) + "/neo_2026-01-01_00-00-00"


def test_create_postgres_backup_task(tmp_path):
    with (
        patch.object(backup_module, "backup_postgres", return_value="pg.sql"),
        patch.object(backup_module, "backup_neo4j", return_value=str(tmp_path)),
    ):
        result = backup_module.create_postgres_backup.run()
        assert "postgres" in result
        assert "neo4j" in result


def _fake_redis_client(*, set_return: bool):
    client = MagicMock()
    client.set.return_value = set_return
    client.get.return_value = b"some-other-token"
    return client


def test_reconcile_neo4j_runs_when_lock_is_free():
    with (
        patch.object(
            reconcile_module.redis.Redis,
            "from_url",
            return_value=_fake_redis_client(set_return=True),
        ),
        patch.object(
            reconcile_module, "_list_tree_ids", new=AsyncMock(return_value=[])
        ),
    ):
        result = reconcile_module.reconcile_neo4j.run()
        assert result["trees_checked"] == 0
        assert "skipped" not in result


def test_reconcile_neo4j_skips_when_already_locked():
    with (
        patch.object(
            reconcile_module.redis.Redis,
            "from_url",
            return_value=_fake_redis_client(set_return=False),
        ),
        patch.object(reconcile_module, "_list_tree_ids", new=AsyncMock()) as list_ids,
    ):
        result = reconcile_module.reconcile_neo4j.run()
        assert result == {"skipped": "already running"}
        list_ids.assert_not_called()


def test_reconcile_neo4j_proceeds_if_redis_is_unavailable():
    client = MagicMock()
    client.set.side_effect = redis.RedisError("down")
    with (
        patch.object(reconcile_module.redis.Redis, "from_url", return_value=client),
        patch.object(
            reconcile_module, "_list_tree_ids", new=AsyncMock(return_value=[])
        ),
    ):
        result = reconcile_module.reconcile_neo4j.run()
        assert result["trees_checked"] == 0
        assert "skipped" not in result
