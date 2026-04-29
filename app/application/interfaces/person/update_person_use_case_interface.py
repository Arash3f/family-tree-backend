from abc import ABC, abstractmethod

from app.application.dto.person.person_update_dto import (
    PersonUpdateDTO,
    PersonUpdateResponseDTO,
)


class IUpdatePersonUseCase(ABC):
    @abstractmethod
    async def execute(self, dto: PersonUpdateDTO) -> PersonUpdateResponseDTO:
        return NotImplemented
