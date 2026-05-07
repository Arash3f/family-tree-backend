from app.application.dto.marriage.divorce_dto import DivorceDTO
from app.application.services.unit_of_work import UnitOfWork
from app.domain.shared.dto.common_dto import ResultDTO


class DivorceUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: DivorceDTO) -> ResultDTO:
        async with self.uow:
            marriage = await self.uow.marriages.get_or_raise(
                marriage_id=dto.marriage_id
            )

            marriage.divorce(divorced_at=dto.divorced_at)

            await self.uow.marriages.end(
                marriage_id=marriage.safe_id, divorced_at=marriage.safe_divorced_at
            )

            await self.uow.commit()

            return ResultDTO(result="Divorce successfuly added")
