from abc import ABC, abstractmethod

from app.application.dto.user.user_get_dto import (
    UserGetResponseDTO,
)
from app.domain.shared.dto.common_dto import IdDTO


class IGetUserUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: IdDTO) -> UserGetResponseDTO:
        raise NotImplementedError
