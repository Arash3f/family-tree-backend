from app.application.dto.person.person_update_dto import (
    PersonUpdateDTO,
    PersonUpdateField,
    PersonUpdateMapper,
    PersonUpdateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.family_tree_sync_service import FamilyTreeSyncService
from app.domain.entities.person import Gender
from app.domain.exceptions.person_exceptions import InvalidPersonGenderException


class UpdatePersonUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        sync_service: FamilyTreeSyncService | None = None,
    ):
        self.uow = uow
        self.sync_service = sync_service or FamilyTreeSyncService()

    async def execute(self, dto: PersonUpdateDTO) -> PersonUpdateResponseDTO:
        async with self.uow:
            person = await self.uow.persons.get_or_raise(person_id=dto.where.person_id)
            old_father_id = person.father_id
            old_mother_id = person.mother_id

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

            if PersonUpdateField.FATHER_ID in update_data_enum:
                father_id = update_data_enum.pop(PersonUpdateField.FATHER_ID)
                if father_id is None:
                    person.father_id = None
                else:
                    father = await self.uow.persons.get_or_raise(person_id=father_id)
                    if father.gender is not Gender.MALE:
                        raise InvalidPersonGenderException(
                            detail=["father's gender must be male"]
                        )
                    person.set_father(father.safe_id)

            if PersonUpdateField.MOTHER_ID in update_data_enum:
                mother_id = update_data_enum.pop(PersonUpdateField.MOTHER_ID)
                if mother_id is None:
                    person.mother_id = None
                else:
                    mother = await self.uow.persons.get_or_raise(person_id=mother_id)
                    if mother.gender is not Gender.FEMALE:
                        raise InvalidPersonGenderException(
                            detail=["mother's gender must be female"]
                        )
                    person.set_mother(mother.safe_id)

            for field, value in update_data_enum.items():
                setattr(person, field.value, value)

            person = await self.uow.persons.update(person=person)

            await self.uow.commit()

            self.sync_service.update_person(
                person,
                old_father_id=old_father_id,
                old_mother_id=old_mother_id,
            )

            return PersonUpdateMapper.to_response(person=person)
