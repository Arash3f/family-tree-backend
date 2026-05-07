from app.application.services.unit_of_work import UnitOfWork
from app.domain.entities.user import User
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.user_filter_dto import FilterUserQuery


class GetUserListByFilterUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, query: FilterUserQuery) -> PaginatedResult[User]:
        async with self.uow:
            user_list = await self.uow.users.get_list_by_filter(query=query)

            return user_list
