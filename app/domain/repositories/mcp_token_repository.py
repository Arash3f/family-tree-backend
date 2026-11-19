from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.mcp_token import McpToken


class McpTokenRepository(ABC):
    @abstractmethod
    async def create(self, token: McpToken) -> McpToken:
        pass

    @abstractmethod
    async def get(self, token_id: UUID) -> McpToken | None:
        pass

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> McpToken | None:
        pass

    @abstractmethod
    async def update(self, token: McpToken) -> McpToken:
        pass

    @abstractmethod
    async def revoke(self, token_id: UUID, revoked_at: datetime) -> None:
        pass

    @abstractmethod
    async def list_active_by_user(self, user_id: UUID) -> list[McpToken]:
        """Non-revoked tokens for a user, newest first."""
        pass

    @abstractmethod
    async def count_active_by_user(self, user_id: UUID) -> int:
        pass
