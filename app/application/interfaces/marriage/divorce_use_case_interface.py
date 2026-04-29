from abc import ABC, abstractmethod

from app.application.dto.marriage.divorce_dto import DivorceDTO
from app.domain.shared.dto.common_dto import ResultDTO


class IDivorceUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: DivorceDTO) -> ResultDTO:
        raise NotImplementedError
