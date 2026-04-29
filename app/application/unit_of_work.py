from abc import ABC, abstractmethod
from typing import Self

from app.domain.repositories.marriage_repository import MarriageRepository
from app.domain.repositories.person_repository import PersonRepository


class UnitOfWork(ABC):
    persons: PersonRepository
    marriages: MarriageRepository

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
