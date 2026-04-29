from abc import ABC, abstractmethod

from app.domain.entities.marriage import Marriage
from app.domain.shared.dto.marriage_filter_dto import FilterMarriageDTO
from app.domain.shared.dto.pagination_dto import PaginatedResult


class IGetMarriageListByFilterUseCase(ABC):
    @abstractmethod
    async def execute(self, query: FilterMarriageDTO) -> PaginatedResult[Marriage]:
        return NotImplemented
