from app.application.dto.role.role_create_dto import (
    RoleCreateDTO,
    RoleCreateMapper,
    RoleCreateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.role import Role


class CreateRoleUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: RoleCreateDTO) -> RoleCreateResponseDTO:
        async with self.uow:
            permission_ids = []
            if dto.permission_ids:
                for perm_id in dto.permission_ids:
                    perm = await self.uow.permissions.get_or_raise(
                        permission_id=perm_id
                    )
                    permission_ids.append(perm.id)

            role = Role(
                name=dto.name,
                permission_ids=permission_ids,
            )

            role = await self.uow.roles.create(role)

            await self.uow.commit()

            return RoleCreateMapper.to_response(role)
