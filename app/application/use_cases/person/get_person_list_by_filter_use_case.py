from uuid import UUID

from app.application.dto.person.person_get_dto import (
    PersonGetMapper,
    PersonGetResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.person_photo_service import PersonPhotoService
from app.domain.shared.dto.pagination_dto import PaginatedResult
from app.domain.shared.dto.person_filter_dto import FilterPersonQuery, PersonFilterDTO


class GetPersonListByFilterUseCase:
    def __init__(self, uow: UnitOfWork, photo_service: PersonPhotoService):
        self.uow = uow
        self.photo_service = photo_service

    async def execute(
        self, query: FilterPersonQuery, *, tree_id: UUID
    ) -> PaginatedResult[PersonGetResponseDTO]:
        async with self.uow:
            filters = query.filters or PersonFilterDTO()
            filters.tree_id = tree_id
            query = query.model_copy(update={"filters": filters})

            person_list = await self.uow.persons.get_list_by_filter(query=query)

            items: list[PersonGetResponseDTO] = []
            for person in person_list.items:
                photo_url = self.photo_service.public_url(person.photo_object_key)
                items.append(PersonGetMapper.to_response(person, photo_url=photo_url))

            return PaginatedResult(
                items=items,
                page=person_list.page,
                page_size=person_list.page_size,
                total=person_list.total,
            )
