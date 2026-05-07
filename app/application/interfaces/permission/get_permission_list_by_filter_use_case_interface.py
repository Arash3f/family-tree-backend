from abc import ABC, abstractmethod
from app.domain.entities.permission import Permission
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.permission_filter_dto import FilterPermissionQuery


class IGetPermissionListByFilterUseCase(ABC):
    @abstractmethod
    async def execute(
        self, query: FilterPermissionQuery
    ) -> PaginatedResult[Permission]:
        raise NotImplementedError
