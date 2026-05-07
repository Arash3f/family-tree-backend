from app.application.dto.marriage.marriage_get_dto import (
    MarriageGetMapper,
    MarriageGetResponseDTO,
)
from app.application.services.unit_of_work import UnitOfWork
from app.domain.shared.dto.common_dto import IdDTO


class GetMarriageUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: IdDTO) -> MarriageGetResponseDTO:
        async with self.uow:
            marriage = await self.uow.marriages.get_or_raise(
                marriage_id=dto.id,
            )

            return MarriageGetMapper.to_response(marriage=marriage)
