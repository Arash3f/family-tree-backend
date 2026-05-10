from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class DeletePersonUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: IdDTO) -> ResultDTO:
        async with self.uow:
            person = await self.uow.persons.get_or_raise(person_id=dto.id)

            await self.uow.persons.delete(person_id=person.safe_id)

            await self.uow.commit()

            return ResultDTO(result="Person deleted successfuly")
