from typing import List

from app.application.dto.role.role_create_dto import (
    RoleCreateDTO,
    RoleCreateMapper,
    RoleCreateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.role import Role
from app.domain.exceptions.role_exceptions import RoleNameDuplicatedException


class CreateRoleUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: RoleCreateDTO) -> RoleCreateResponseDTO:
        async with self.uow:
            is_duplicated = await self.uow.roles.is_role_name_duplicated(
                role_name=dto.name
            )

            if is_duplicated:
                raise RoleNameDuplicatedException()

            permission_ids: List[int] = []
            if dto.permission_ids:
                for perm_id in dto.permission_ids:
                    perm = await self.uow.permissions.get_or_raise(
                        permission_id=perm_id
                    )
                    permission_ids.append(perm.safe_id)

            role = Role(
                name=dto.name,
                permission_ids=permission_ids,
            )

            role = await self.uow.roles.create(role)

            await self.uow.commit()

            return RoleCreateMapper.to_response(role)
