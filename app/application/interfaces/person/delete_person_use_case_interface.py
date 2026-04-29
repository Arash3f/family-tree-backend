from abc import ABC, abstractmethod

from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class IDeletePersonUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: IdDTO) -> ResultDTO:
        return NotImplemented
