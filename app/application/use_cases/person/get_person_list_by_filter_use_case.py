from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.person import Person
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.person_filter_dto import FilterPersonQuery


class GetPersonListByFilterUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, query: FilterPersonQuery) -> PaginatedResult[Person]:
        async with self.uow:
            person_list = await self.uow.persons.get_list_by_filter(query=query)

            return person_list
