from app.application.dto.person.person_get_dto import (
    PersonGetMapper,
    PersonGetResponseDTO,
)
from app.application.services.unit_of_work import UnitOfWork
from app.domain.shared.dto.common_dto import IdDTO


class GetPersonUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: IdDTO) -> PersonGetResponseDTO:
        async with self.uow:
            person = await self.uow.persons.get_or_raise(person_id=dto.id)

            return PersonGetMapper.to_response(person=person)
