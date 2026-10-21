from abc import ABC, abstractmethod
from uuid import UUID


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, user_id: UUID, session_id: UUID) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, user_id: UUID, session_id: UUID) -> str:
        pass

    @abstractmethod
    def create_impersonation_token(
        self, target_user_id: UUID, actor_admin_id: UUID
    ) -> str:
        pass

    @abstractmethod
    def decode_token(self, token: str) -> dict:
        pass

    @abstractmethod
    def hash_token(self, token: str) -> str:
        pass
