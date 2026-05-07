from app.application.services.unit_of_work import UnitOfWork
from app.domain.entities.permission import Permission
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.permission_filter_dto import FilterPermissionQuery


class GetPermissionListByFilterUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self, query: FilterPermissionQuery
    ) -> PaginatedResult[Permission]:
        async with self.uow:
            permission_list = await self.uow.permissions.get_list_by_filter(query=query)

            return permission_list
