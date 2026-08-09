from app.application.dto.person.person_create_dto import (
    ParentLinkDTO,
    PersonCreateMapper,
)
from app.application.dto.person.person_update_dto import (
    PersonUpdateDTO,
    PersonUpdateField,
    PersonUpdateMapper,
    PersonUpdateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.application.services.person_photo_service import PersonPhotoService
from app.domain.entities.person import ParentRelationshipType
from app.domain.exceptions.person_exceptions import (
    InvalidParentMarriageException,
    InvalidPersonGenderException,
)


class UpdatePersonUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        photo_service: PersonPhotoService,
        sync_service: FamilyTreeSyncService | None = None,
    ):
        self.uow = uow
        self.photo_service = photo_service
        self.sync_service = sync_service or FamilyTreeSyncService()

    async def execute(self, dto: PersonUpdateDTO) -> PersonUpdateResponseDTO:
        async with self.uow:
            person = await self.uow.persons.get_or_raise(person_id=dto.where.person_id)
            old_parent_ids = set(person.parent_ids)
            old_photo_key = person.photo_object_key
            photo_key_to_delete: str | None = None

            update_data = dto.data.model_dump(exclude_unset=True)

            update_data_enum = {
                PersonUpdateField(key): value for key, value in update_data.items()
            }

            if PersonUpdateField.GENDER in update_data_enum:
                new_gender = update_data_enum[PersonUpdateField.GENDER]
                if (
                    new_gender != person.gender
                    and await self.uow.marriages.has_active_for_person(person.safe_id)
                ):
                    raise InvalidPersonGenderException(
                        detail=[
                            "cannot change gender while person has an active marriage"
                        ]
                    )

            if PersonUpdateField.PARENTS in update_data_enum:
                parents_data = update_data_enum.pop(PersonUpdateField.PARENTS) or []
                parents = PersonCreateMapper.to_domain_parents(
                    [ParentLinkDTO.model_validate(item) for item in parents_data]
                )
                for link in parents:
                    await self.uow.persons.get_or_raise(person_id=link.parent_id)
                person.set_parents(parents)

            if PersonUpdateField.MARRIAGE_ID in update_data_enum:
                marriage_id = update_data_enum.pop(PersonUpdateField.MARRIAGE_ID)
                if marriage_id is not None:
                    await self.uow.marriages.get_or_raise(marriage_id=marriage_id)
                person.marriage_id = marriage_id

            if person.marriage_id is not None:
                marriage = await self.uow.marriages.get_or_raise(
                    marriage_id=person.marriage_id
                )
                spouse_ids = {marriage.husband_id, marriage.wife_id}
                for link in person.parents:
                    if (
                        link.relationship_type is ParentRelationshipType.BIOLOGICAL
                        and link.parent_id not in spouse_ids
                    ):
                        raise InvalidParentMarriageException()

            if PersonUpdateField.PHOTO_OBJECT_KEY in update_data_enum:
                new_photo_key = update_data_enum.pop(PersonUpdateField.PHOTO_OBJECT_KEY)
                if new_photo_key is not None:
                    await self.photo_service.ensure_object_exists(new_photo_key)
                if old_photo_key and old_photo_key != new_photo_key:
                    photo_key_to_delete = old_photo_key
                person.photo_object_key = new_photo_key

            for field, value in update_data_enum.items():
                setattr(person, field.value, value)

            person = await self.uow.persons.update(person=person)

            await self.uow.commit()

            self.sync_service.update_person(
                person,
                old_parent_ids=old_parent_ids,
            )

            await self.photo_service.delete_quiet(photo_key_to_delete)

            photo_url = await self.photo_service.presign(person.photo_object_key)
            return PersonUpdateMapper.to_response(person=person, photo_url=photo_url)
