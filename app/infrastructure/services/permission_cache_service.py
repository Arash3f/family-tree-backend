from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork


class PermissionCacheService:
    """Cache user permissions in memory with TTL to reduce DB queries."""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[UUID, tuple[set[str], datetime]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    async def get_permissions(
        self, user_id: UUID, uow: UnitOfWork
    ) -> set[str]:
        """Get user permissions with cache, TTL 1 hour by default."""
        now = datetime.now(timezone.utc)

        if user_id in self._cache:
            permissions, expiry = self._cache[user_id]
            if now < expiry:
                return permissions

        async with uow:
            user = await uow.users.get(user_id)
            if not user or not user.role_id:
                self._cache[user_id] = (set(), now + self.ttl)
                return set()

            role = await uow.roles.get(user.role_id)
            if not role:
                self._cache[user_id] = (set(), now + self.ttl)
                return set()

            permissions = await uow.permissions.get_list()
            role_permission_ids = set(role.permission_ids)
            permission_names = {
                p.name for p in permissions if p.id in role_permission_ids
            }

            self._cache[user_id] = (permission_names, now + self.ttl)
            return permission_names

    def invalidate(self, user_id: UUID) -> None:
        """Clear cache for a specific user."""
        self._cache.pop(user_id, None)

    def clear(self) -> None:
        """Clear all cached permissions."""
        self._cache.clear()
