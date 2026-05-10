from abc import ABC, abstractmethod
from typing import Self

from app.domain.repositories.marriage_repository import MarriageRepository
from app.domain.repositories.permission_repository import PermissionRepository
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.role_repository import RoleRepository
from app.domain.repositories.user_repository import UserRepository


class UnitOfWork(ABC):
    persons: PersonRepository
    marriages: MarriageRepository
    permissions: PermissionRepository
    users: UserRepository
    roles: RoleRepository

    async def __aenter__(self) -> Self:
        return self

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb):
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass
