from app.application.dto.role.role_get_dto import (
    RoleGetMapper,
    RoleGetResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.shared.dto.common_dto import IdDTO


class GetRoleUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: IdDTO) -> RoleGetResponseDTO:
        async with self.uow:
            role = await self.uow.roles.get_or_raise(role_id=dto.id)

            return RoleGetMapper.to_response(role=role)
