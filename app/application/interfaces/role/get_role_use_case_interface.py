from abc import ABC, abstractmethod
from app.application.dto.role.role_get_dto import (
    RoleGetResponseDTO,
)
from app.domain.shared.dto.common_dto import IdDTO


class IGetRoleUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: IdDTO) -> RoleGetResponseDTO:
        raise NotImplementedError
