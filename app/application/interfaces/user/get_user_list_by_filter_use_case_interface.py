from abc import ABC, abstractmethod
from app.domain.entities.user import User
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.user_filter_dto import FilterUserQuery


class IGetUserListByFilterUseCase(ABC):
    @abstractmethod
    async def execute(self, query: FilterUserQuery) -> PaginatedResult[User]:
        raise NotImplementedError
