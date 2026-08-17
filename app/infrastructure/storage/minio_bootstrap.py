from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.infrastructure.storage.minio_object_storage import MinioObjectStorage

logger = logging.getLogger(__name__)


async def ensure_minio_buckets(
    *,
    retries: int = 5,
    retry_delay_seconds: float = 2.0,
) -> None:
    """Ensure configured MinIO buckets exist (private by default)."""
    bucket_names = settings.minio_buckets
    storage = MinioObjectStorage()
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            await storage.ensure_buckets(bucket_names)
            return
        except (ConnectionError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            logger.warning(
                "MinIO bucket bootstrap failed (attempt %s/%s): %s",
                attempt,
                retries,
                exc,
            )
            await asyncio.sleep(retry_delay_seconds)

    assert last_error is not None
    raise last_error
