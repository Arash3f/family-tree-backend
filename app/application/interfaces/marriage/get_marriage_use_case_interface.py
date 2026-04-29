from abc import ABC, abstractmethod

from app.application.dto.marriage.marriage_get_dto import MarriageGetResponseDTO
from app.domain.shared.dto.common_dto import IdDTO


class IGetMarriageUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: IdDTO) -> MarriageGetResponseDTO:
        raise NotImplementedError
