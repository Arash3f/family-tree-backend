from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import AppSettings
from app.infrastructure.storage.minio_bootstrap import ensure_minio_buckets


def _base_kwargs(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "JWT_SECRET": "local-dev-only-change-me-32chars-min",
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_PORT": 5432,
        "POSTGRES_DB": "family_tree",
        "POSTGRES_HOST_TEST": "127.0.0.1",
        "POSTGRES_PORT_TEST": 5432,
        "POSTGRES_DB_TEST": "family_tree_test",
    }
    data.update(overrides)
    return data


def test_minio_buckets_default_to_minio_bucket(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MINIO_BUCKETS", raising=False)
    settings = AppSettings(_env_file=None, **_base_kwargs(MINIO_BUCKET="photos"))  # type: ignore[call-arg]
    assert settings.minio_buckets == ["photos"]


def test_minio_buckets_parse_comma_separated_list():
    settings = AppSettings(
        _env_file=None,  # type: ignore[call-arg]
        **_base_kwargs(MINIO_BUCKET="photos", MINIO_BUCKETS="photos, backups ,exports"),
    )
    assert settings.minio_buckets == ["photos", "backups", "exports"]


def test_minio_bucket_must_be_listed_in_minio_buckets():
    with pytest.raises(
        ValueError, match="MINIO_BUCKET 'photos' must appear in MINIO_BUCKETS"
    ):
        AppSettings(
            _env_file=None,  # type: ignore[call-arg]
            **_base_kwargs(MINIO_BUCKET="photos", MINIO_BUCKETS="exports"),
        )


@pytest.mark.asyncio
async def test_ensure_minio_buckets_retries_until_success():
    storage = MagicMock()
    storage.ensure_buckets = AsyncMock(side_effect=[ConnectionError("down"), None])

    with (
        patch(
            "app.infrastructure.storage.minio_bootstrap.MinioObjectStorage",
            return_value=storage,
        ),
        patch(
            "app.infrastructure.storage.minio_bootstrap.asyncio.sleep", new=AsyncMock()
        ),
    ):
        await ensure_minio_buckets(retries=2, retry_delay_seconds=0)

    assert storage.ensure_buckets.await_count == 2


@pytest.mark.asyncio
async def test_ensure_minio_buckets_raises_after_retries_exhausted():
    storage = MagicMock()
    storage.ensure_buckets = AsyncMock(side_effect=ConnectionError("still down"))

    with (
        patch(
            "app.infrastructure.storage.minio_bootstrap.MinioObjectStorage",
            return_value=storage,
        ),
        patch(
            "app.infrastructure.storage.minio_bootstrap.asyncio.sleep", new=AsyncMock()
        ),
        pytest.raises(ConnectionError, match="still down"),
    ):
        await ensure_minio_buckets(retries=2, retry_delay_seconds=0)

    assert storage.ensure_buckets.await_count == 2
