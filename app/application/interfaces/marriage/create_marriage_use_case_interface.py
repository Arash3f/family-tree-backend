from abc import ABC, abstractmethod

from app.application.dto.marriage.marriage_create_dto import (
    MarriageCreateDTO,
    MarriageCreateResponseDTO,
)


class ICreateMarriageUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: MarriageCreateDTO) -> MarriageCreateResponseDTO:
        raise NotImplementedError
