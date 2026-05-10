from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class DeleteRoleUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: IdDTO) -> ResultDTO:
        async with self.uow:
            role = await self.uow.roles.get_or_raise(role_id=dto.id)

            await self.uow.roles.delete(role_id=role.safe_id)

            await self.uow.commit()

            return ResultDTO(result="Role deleted successfuly")
