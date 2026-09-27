from uuid import UUID

from app.application.dto.person.person_card_dto import (
    PersonCardResponseDTO,
    build_person_card,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.person_photo_service import PersonPhotoService
from app.domain.shared.dto.common_dto import IdDTO


class GetPersonCardUseCase:
    """Assemble the pedigree person-detail card in one round-trip."""

    def __init__(self, uow: UnitOfWork, photo_service: PersonPhotoService):
        self.uow = uow
        self.photo_service = photo_service

    async def execute(self, dto: IdDTO, *, tree_id: UUID) -> PersonCardResponseDTO:
        async with self.uow:
            person = await self.uow.persons.get_in_tree_or_raise(
                person_id=dto.id, tree_id=tree_id
            )
            tree_people = await self.uow.persons.get_by_tree_id(tree_id)
            marriages = await self.uow.marriages.get_by_person_ids([person.safe_id])

            def photo_url_of(item) -> str | None:
                return self.photo_service.media_url(item.photo_object_key)

            return build_person_card(
                person,
                tree_people=tree_people,
                marriages=marriages,
                photo_url_of=photo_url_of,
            )
