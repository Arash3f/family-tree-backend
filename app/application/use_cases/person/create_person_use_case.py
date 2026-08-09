from app.application.dto.person.person_create_dto import (
    PersonCreateDTO,
    PersonCreateMapper,
    PersonCreateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.application.services.person_photo_service import PersonPhotoService
from app.domain.entities.person import ParentRelationshipType, Person
from app.domain.exceptions.person_exceptions import InvalidParentMarriageException


class CreatePersonUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        photo_service: PersonPhotoService,
        sync_service: FamilyTreeSyncService | None = None,
    ):
        self.uow = uow
        self.photo_service = photo_service
        self.sync_service = sync_service or FamilyTreeSyncService()

    async def execute(self, dto: PersonCreateDTO) -> PersonCreateResponseDTO:
        async with self.uow:
            parents = PersonCreateMapper.to_domain_parents(dto.parents)

            for link in parents:
                await self.uow.persons.get_or_raise(person_id=link.parent_id)

            if dto.marriage_id is not None:
                marriage = await self.uow.marriages.get_or_raise(
                    marriage_id=dto.marriage_id
                )
                spouse_ids = {marriage.spouse_a_id, marriage.spouse_b_id}
                for link in parents:
                    if (
                        link.relationship_type is ParentRelationshipType.BIOLOGICAL
                        and link.parent_id not in spouse_ids
                    ):
                        raise InvalidParentMarriageException()

            if dto.photo_object_key is not None:
                await self.photo_service.ensure_object_exists(dto.photo_object_key)

            person = Person(
                id=None,
                name=dto.name,
                gender=dto.gender,
                birth_date=dto.birth_date,
                death_date=dto.death_date,
                family_name=dto.family_name,
                birth_place=dto.birth_place,
                death_place=dto.death_place,
                notes=dto.notes,
                parents=parents,
                marriage_id=dto.marriage_id,
                photo_object_key=dto.photo_object_key,
            )

            person = await self.uow.persons.create(person)

            await self.uow.commit()

            self.sync_service.upsert_person(person)

            photo_url = await self.photo_service.presign(person.photo_object_key)
            return PersonCreateMapper.to_response(person, photo_url=photo_url)
