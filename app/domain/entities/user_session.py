from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from app.domain.exceptions.common_exceptions import UnExpectedIdException


@dataclass
class UserSession:
    """Persistent login session bound to a refresh token."""

    user_id: UUID
    refresh_token_hash: str
    expires_at: datetime
    id: UUID | None = None
    revoked_at: datetime | None = None
    replaced_by_id: UUID | None = None
    user_agent: str | None = None
    ip_address: str | None = None
    created_at: datetime | None = None

    def is_active(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        if self.revoked_at is not None:
            return False
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires > now

    def revoke(self, now: datetime | None = None) -> None:
        self.revoked_at = now or datetime.now(timezone.utc)

    @property
    def safe_id(self) -> UUID:
        if self.id is None:
            raise UnExpectedIdException(detail=["session has no id"])
        return self.id
