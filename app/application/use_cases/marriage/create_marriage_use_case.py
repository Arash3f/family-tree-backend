from app.application.dto.marriage.marriage_create_dto import (
    MarriageCreateDTO,
    MarriageCreateMapper,
    MarriageCreateResponseDTO,
)
from app.application.unit_of_work import UnitOfWork
from app.domain.entities.marriage import Marriage


class CreateMarriageUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: MarriageCreateDTO) -> MarriageCreateResponseDTO:
        async with self.uow:
            await self.uow.persons.get_or_raise(person_id=dto.husband_id)
            await self.uow.persons.get_or_raise(person_id=dto.wife_id)

            marriage = Marriage(
                id=None,
                husband_id=dto.husband_id,
                wife_id=dto.wife_id,
                married_at=dto.married_at,
            )

            marriage = await self.uow.marriages.create(marriage)

            await self.uow.commit()

            return MarriageCreateMapper.to_response(marriage=marriage)
