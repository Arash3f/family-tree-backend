from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.exceptions.role_exceptions import RoleProtectedException
from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class DeleteRoleUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: IdDTO) -> ResultDTO:
        async with self.uow:
            role = await self.uow.roles.get_or_raise(role_id=dto.id)

            if role.name.strip().lower() == settings.ADMIN_ROLE_NAME.strip().lower():
                raise RoleProtectedException()

            await self.uow.roles.delete(role_id=role.safe_id)

            await self.uow.commit()

            return ResultDTO(result="Role deleted successfully")
