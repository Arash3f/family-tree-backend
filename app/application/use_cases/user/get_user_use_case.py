from app.application.dto.user.user_get_dto import (
    UserGetMapper,
    UserGetResponseDTO,
)
from app.application.services.unit_of_work import UnitOfWork
from app.domain.shared.dto.common_dto import IdDTO


class GetUserUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: IdDTO) -> UserGetResponseDTO:
        async with self.uow:
            user = await self.uow.users.get_or_raise(user_id=dto.id)

            return UserGetMapper.to_response(user=user)
