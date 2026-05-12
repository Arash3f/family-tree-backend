from typing import List

from app.application.dto.role.role_update_dto import (
    RoleUpdateDTO,
    RoleUpdateField,
    RoleUpdateMapper,
    RoleUpdateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.role_exceptions import RoleNameDuplicatedException


class UpdateRoleUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, dto: RoleUpdateDTO) -> RoleUpdateResponseDTO:
        async with self.uow:
            if dto.data.name:
                is_role_name_duplicated = await self.uow.roles.is_role_name_duplicated(
                    exception_role_id=dto.where.role_id, role_name=dto.data.name
                )
                if is_role_name_duplicated:
                    raise RoleNameDuplicatedException()

            role = await self.uow.roles.get_or_raise(role_id=dto.where.role_id)

            update_data = dto.data.model_dump(exclude_unset=True, exclude_none=True)

            update_data_enum = {
                RoleUpdateField(key): value for key, value in update_data.items()
            }

            permission_ids = update_data_enum.pop(RoleUpdateField.PERMISSION_IDS, None)

            if permission_ids is not None:
                permissions: List[int] = []
                for perm_id in permission_ids:
                    perm = await self.uow.permissions.get_or_raise(
                        permission_id=perm_id
                    )
                    permissions.append(perm.safe_id)
                role.permission_ids = permissions

            for field, value in update_data_enum.items():
                setattr(role, field.value, value)

            role = await self.uow.roles.update(role=role)

            await self.uow.commit()

            return RoleUpdateMapper.to_response(role=role)
