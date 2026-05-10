from abc import ABC, abstractmethod

from app.application.dto.role.role_update_dto import (
    RoleUpdateDTO,
    RoleUpdateResponseDTO,
)


class IUpdateRoleUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: RoleUpdateDTO) -> RoleUpdateResponseDTO:
        raise NotImplementedError
