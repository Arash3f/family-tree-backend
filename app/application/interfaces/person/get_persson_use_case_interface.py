from abc import ABC, abstractmethod

from app.application.dto.person.person_get_dto import PersonGetResponseDTO
from app.domain.shared.dto.common_dto import IdDTO


class IGetPersonUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: IdDTO) -> PersonGetResponseDTO:
        return NotImplemented
