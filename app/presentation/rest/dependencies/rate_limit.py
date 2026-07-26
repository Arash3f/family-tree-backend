from collections import defaultdict
from time import monotonic

from fastapi import HTTPException, Request

from app.core.config import settings

_attempts: dict[str, list[float]] = defaultdict(list)


async def rate_limit_auth(request: Request) -> None:
    """Simple per-IP sliding window for unauthenticated auth endpoints."""
    limit = settings.AUTH_RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return

    ip = request.client.host if request.client else "unknown"
    now = monotonic()
    window_start = now - 60
    recent = [t for t in _attempts[ip] if t >= window_start]
    if len(recent) >= limit:
        _attempts[ip] = recent
        raise HTTPException(status_code=429, detail="Too many authentication attempts")

    recent.append(now)
    _attempts[ip] = recent