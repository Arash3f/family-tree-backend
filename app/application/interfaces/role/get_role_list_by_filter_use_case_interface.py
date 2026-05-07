from abc import ABC, abstractmethod
from app.domain.entities.role import Role
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.role_filter_dto import FilterRoleQuery


class IGetRoleListByFilterUseCase(ABC):
    @abstractmethod
    async def execute(self, query: FilterRoleQuery) -> PaginatedResult[Role]:
        raise NotImplementedError
