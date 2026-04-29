from app.application.dto.person.person_update_dto import (
    PersonUpdateDTO,
    PersonUpdateField,
    PersonUpdateMapper,
    PersonUpdateResponseDTO,
)
from app.application.unit_of_work import UnitOfWork


class UpdatePersonUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: PersonUpdateDTO) -> PersonUpdateResponseDTO:
        async with self.uow:
            person = await self.uow.persons.get_or_raise(person_id=dto.where.person_id)

            update_data = dto.data.model_dump(exclude_unset=True, exclude_none=True)

            update_data_enum = {
                PersonUpdateField(key): value for key, value in update_data.items()
            }

            father_id = update_data_enum.pop(PersonUpdateField.FATHER_ID, None)
            mother_id = update_data_enum.pop(PersonUpdateField.MOTHER_ID, None)

            if father_id is not None:
                father = await self.uow.persons.get_or_raise(father_id)
                person.set_father(father.safe_id)

            if mother_id is not None:
                mother = await self.uow.persons.get_or_raise(mother_id)
                person.set_mother(mother.safe_id)

            for field, value in update_data_enum.items():
                setattr(person, field.value, value)

            person = await self.uow.persons.update(person=person)

            await self.uow.commit()

            return PersonUpdateMapper.to_response(person=person)
