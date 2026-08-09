from time import time
from urllib.parse import urlparse

import redis
import redis.asyncio as aioredis
from fastapi import HTTPException, Request

from app.core.config import settings

_redis_client: aioredis.Redis | None = None


def _rate_limit_redis_url() -> str:
    """Use Celery broker host with a dedicated Redis DB for auth rate limits."""
    parsed = urlparse(settings.CELERY_BROKER_URL)
    # redis://host:6379/0 -> redis://host:6379/2
    path = "/2"
    netloc = parsed.netloc or "127.0.0.1:6379"
    scheme = parsed.scheme or "redis"
    return f"{scheme}://{netloc}{path}"


def get_rate_limit_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.Redis.from_url(
            _rate_limit_redis_url(),
            decode_responses=True,
        )
    return _redis_client


async def reset_rate_limit_redis() -> None:
    """Drop the cached client so the next call reconnects (used by tests)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def rate_limit_auth(request: Request) -> None:
    """Per-IP sliding window for unauthenticated auth endpoints (shared via Redis).

    When Redis is unreachable the limiter cannot tell a first attempt from the
    ten-thousandth, so outside development it refuses the request rather than
    leaving credential stuffing unmetered. Locally it stays permissive so a
    missing Redis does not block day-to-day work.
    """
    limit = settings.AUTH_RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return

    ip = request.client.host if request.client else "unknown"
    now = time()
    window_start = now - 60
    key = f"auth_rate:{ip}"
    client = get_rate_limit_redis()

    try:
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {f"{now}": now})
        pipe.zcard(key)
        pipe.expire(key, 60)
        _removed, _added, count, _expire = await pipe.execute()
    except (redis.RedisError, OSError) as exc:
        if settings.is_development_like:
            return
        raise HTTPException(
            status_code=503,
            detail="Authentication is temporarily unavailable",
        ) from exc

    if int(count) > limit:
        raise HTTPException(status_code=429, detail="Too many authentication attempts")
