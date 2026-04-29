from abc import ABC, abstractmethod

from app.domain.entities.person import Person
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.person_filter_dto import FilterPersonQuery


class IGetPersonListByFilterUseCase(ABC):
    @abstractmethod
    async def execute(self, query: FilterPersonQuery) -> PaginatedResult[Person]:
        return NotImplemented
