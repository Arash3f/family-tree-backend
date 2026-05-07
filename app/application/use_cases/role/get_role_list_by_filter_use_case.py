from app.application.services.unit_of_work import UnitOfWork
from app.domain.entities.role import Role
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.role_filter_dto import FilterRoleQuery


class GetRoleListByFilterUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, query: FilterRoleQuery) -> PaginatedResult[Role]:
        async with self.uow:
            role_list = await self.uow.roles.get_list_by_filter(query=query)

            return role_list
