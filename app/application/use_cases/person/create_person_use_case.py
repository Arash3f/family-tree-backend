from app.application.dto.person.person_create_dto import (
    PersonCreateDTO,
    PersonCreateMapper,
    PersonCreateResponseDTO,
)
from app.application.services.unit_of_work import UnitOfWork
from app.domain.entities.person import Gender, Person
from app.domain.exceptions.person_exceptions import InvalidPersonGenderException


class CreatePersonUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: PersonCreateDTO) -> PersonCreateResponseDTO:
        async with self.uow:
            if dto.father_id is not None:
                father = await self.uow.persons.get_or_raise(person_id=dto.father_id)
                if father.gender is not Gender.MALE:
                    raise InvalidPersonGenderException(
                        detail=["father's gender musst be male"]
                    )

            if dto.mother_id is not None:
                mother = await self.uow.persons.get_or_raise(person_id=dto.mother_id)
                if mother.gender is not Gender.FEMALE:
                    raise InvalidPersonGenderException(
                        detail=["mother's gender must be female"]
                    )

            person = Person(
                id=None,
                name=dto.name,
                gender=dto.gender,
                birth_date=dto.birth_date,
                mother_id=dto.mother_id,
                father_id=dto.father_id,
            )

            person = await self.uow.persons.create(person)

            await self.uow.commit()

            return PersonCreateMapper.to_response(person)
