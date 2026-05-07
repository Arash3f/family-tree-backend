from app.application.services.unit_of_work import UnitOfWork
from app.domain.entities.marriage import Marriage
from app.domain.shared.dto.marriage_filter_dto import FilterMarriageDTO
from app.domain.shared.dto.pagination_dto import PaginatedResult


class GetMarriageListByFilterUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, query: FilterMarriageDTO) -> PaginatedResult[Marriage]:
        async with self.uow:
            person_list = await self.uow.marriages.get_list_by_filter(query=query)

            return person_list
