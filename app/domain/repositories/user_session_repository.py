from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.user_session import UserSession


class UserSessionRepository(ABC):
    @abstractmethod
    async def create(self, session: UserSession) -> UserSession:
        pass

    @abstractmethod
    async def get(self, session_id: UUID) -> UserSession | None:
        pass

    @abstractmethod
    async def get_for_update(self, session_id: UUID) -> UserSession | None:
        """Load session row with a write lock for refresh rotation."""
        pass

    @abstractmethod
    async def update(self, session: UserSession) -> UserSession:
        pass

    @abstractmethod
    async def revoke(self, session_id: UUID, revoked_at: datetime) -> None:
        pass

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID, revoked_at: datetime) -> int:
        pass
