from abc import abstractmethod

from app.application.dto.person.person_create_dto import (
    PersonCreateDTO,
    PersonCreateResponseDTO,
)


class ICreatePersonUseCase:
    @abstractmethod
    async def execute(self, dto: PersonCreateDTO) -> PersonCreateResponseDTO:
        return NotImplemented
