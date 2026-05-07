from abc import ABC, abstractmethod
from app.application.dto.user.user_create_dto import (
    UserCreateDTO,
    UserCreateResponseDTO,
)


class ICreateUserUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: UserCreateDTO) -> UserCreateResponseDTO:
        raise NotImplementedError
