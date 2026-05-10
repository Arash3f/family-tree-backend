from abc import ABC, abstractmethod

from app.application.dto.role.role_create_dto import (
    RoleCreateDTO,
    RoleCreateResponseDTO,
)


class ICreateRoleUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: RoleCreateDTO) -> RoleCreateResponseDTO:
        raise NotImplementedError
