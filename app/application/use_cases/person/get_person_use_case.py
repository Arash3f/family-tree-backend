from uuid import UUID

from app.application.dto.person.person_get_dto import (
    PersonGetMapper,
    PersonGetResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.person_photo_service import PersonPhotoService
from app.domain.shared.dto.common_dto import IdDTO


class GetPersonUseCase:
    def __init__(self, uow: UnitOfWork, photo_service: PersonPhotoService):
        self.uow = uow
        self.photo_service = photo_service

    async def execute(self, dto: IdDTO, *, tree_id: UUID) -> PersonGetResponseDTO:
        async with self.uow:
            person = await self.uow.persons.get_in_tree_or_raise(
                person_id=dto.id, tree_id=tree_id
            )
            photo_url = await self.photo_service.presign(person.photo_object_key)
            return PersonGetMapper.to_response(person=person, photo_url=photo_url)
