from datetime import datetime, timedelta, timezone
from typing import NamedTuple
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork


class _CachedPermissions(NamedTuple):
    permissions: set[str]
    expires_at: datetime


class PermissionCacheService:
    """In-memory permission caching with TTL expiration."""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[UUID, _CachedPermissions] = {}
        self._ttl_seconds = ttl_seconds

    async def get_permissions(self, user_id: UUID, uow: UnitOfWork) -> set[str]:
        now = datetime.now(timezone.utc)
        cached = self._cache.get(user_id)
        if cached and cached.expires_at > now:
            return cached.permissions

        async with uow:
            user = await uow.users.get_with_details(user_id)
            permissions = set()
            if user and user.role:
                permissions = {p.name for p in user.role.permissions}

        expires_at = now + timedelta(seconds=self._ttl_seconds)
        self._cache[user_id] = _CachedPermissions(permissions, expires_at)
        return permissions

    def invalidate(self, user_id: UUID) -> None:
        self._cache.pop(user_id, None)

    def clear(self) -> None:
        self._cache.clear()
