from app.application.services.unit_of_work import UnitOfWork
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class DeleteMarriageUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: IdDTO) -> ResultDTO:
        async with self.uow:
            marriage = await self.uow.marriages.get_or_raise(marriage_id=dto.id)

            await self.uow.marriages.delete(marriage_id=marriage.safe_id)

            await self.uow.commit()

            return ResultDTO(result="Marriage deleted successfuly")
