from abc import ABC, abstractmethod

from app.domain.shared.dto.common_dto import IdDTO, ResultDTO


class IDeleteRoleUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: IdDTO) -> ResultDTO:
        raise NotImplementedError
