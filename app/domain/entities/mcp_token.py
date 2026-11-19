from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.domain.exceptions.common_exceptions import UnExpectedIdException


@dataclass
class McpToken:
    """Long-lived personal access token for the MCP endpoint."""

    user_id: UUID
    name: str
    token_hash: str
    token_prefix: str
    id: UUID | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime | None = None

    def is_active(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(UTC)
        if self.revoked_at is not None:
            return False
        if self.expires_at is None:
            return True
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        return expires > now

    def revoke(self, now: datetime | None = None) -> None:
        self.revoked_at = now or datetime.now(UTC)

    def touch(self, now: datetime | None = None) -> None:
        self.last_used_at = now or datetime.now(UTC)

    @property
    def safe_id(self) -> UUID:
        if self.id is None:
            raise UnExpectedIdException(detail=["mcp token has no id"])
        return self.id
