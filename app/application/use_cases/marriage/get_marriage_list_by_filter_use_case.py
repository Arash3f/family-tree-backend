from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.marriage import Marriage
from app.domain.shared.dto.marriage_filter_dto import (
    FilterMarriageDTO,
    MarriageFilterDataDTO,
)
from app.domain.shared.dto.pagination_dto import PaginatedResult


class GetMarriageListByFilterUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self, query: FilterMarriageDTO, *, tree_id: UUID
    ) -> PaginatedResult[Marriage]:
        async with self.uow:
            filters = query.filters or MarriageFilterDataDTO()
            filters.tree_id = tree_id
            query = query.model_copy(update={"filters": filters})
            return await self.uow.marriages.get_list_by_filter(query=query)
