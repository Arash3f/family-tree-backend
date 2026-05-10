from abc import ABC, abstractmethod

from app.application.dto.user.user_update_dto import (
    UserUpdateDTO,
    UserUpdateResponseDTO,
)


class IUpdateUserUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: UserUpdateDTO) -> UserUpdateResponseDTO:
        raise NotImplementedError
