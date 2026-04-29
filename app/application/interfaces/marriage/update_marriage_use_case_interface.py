from abc import ABC, abstractmethod

from app.application.dto.marriage.marriage_update_dto import (
    MarriageUpdateDTO,
    MarriageUpdateResponseDTO,
)


class IUpdateMarriageUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: MarriageUpdateDTO) -> MarriageUpdateResponseDTO:
        raise NotImplementedError
