from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class DeleteUserUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: IdDTO) -> ResultDTO:
        async with self.uow:
            user = await self.uow.users.get_or_raise(user_id=dto.id)

            await self.uow.users.delete(user_id=user.safe_id)

            await self.uow.commit()

            return ResultDTO(result="User deleted successfuly")
