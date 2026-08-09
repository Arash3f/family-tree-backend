from time import time
from urllib.parse import urlparse

import redis
from fastapi import HTTPException, Request

from app.core.config import settings

_redis_client: redis.Redis | None = None


def _rate_limit_redis_url() -> str:
    """Use Celery broker host with a dedicated Redis DB for auth rate limits."""
    parsed = urlparse(settings.CELERY_BROKER_URL)
    # redis://host:6379/0 -> redis://host:6379/2
    path = "/2"
    netloc = parsed.netloc or "127.0.0.1:6379"
    scheme = parsed.scheme or "redis"
    return f"{scheme}://{netloc}{path}"


def get_rate_limit_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            _rate_limit_redis_url(),
            decode_responses=True,
        )
    return _redis_client


async def rate_limit_auth(request: Request) -> None:
    """Per-IP sliding window for unauthenticated auth endpoints (shared via Redis)."""
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
        _removed, _added, count, _expire = pipe.execute()
    except redis.RedisError:
        # Fail open if Redis is temporarily unavailable so login is not bricked.
        return

    if int(count) > limit:
        raise HTTPException(status_code=429, detail="Too many authentication attempts")
