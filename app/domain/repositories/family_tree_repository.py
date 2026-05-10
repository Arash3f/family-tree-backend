from abc import ABC, abstractmethod

from app.domain.shared.dto.family_tree_dto import (
    DeleteRelationshipDTO,
    DeleteSpouseRelationshipDTO,
    ParentRelationshipDTO,
    ParentRelationshipResponseDTO,
    PersonIdDTO,
    PersonResponseDTO,
    PersonUpsertDTO,
    SpouseRelationshipDTO,
    SpouseRelationshipResponseDTO,
)


class FamilyTreeRepository(ABC):
    # -------------------------
    # Person CRUD
    # -------------------------

    @abstractmethod
    def upsert_person(self, data: PersonUpsertDTO) -> PersonResponseDTO:
        pass

    @abstractmethod
    def delete_person(self, data: PersonIdDTO) -> bool:
        pass

    @abstractmethod
    def get_person(self, data: PersonIdDTO) -> PersonResponseDTO:
        pass

    @abstractmethod
    def person_exists(self, data: PersonIdDTO) -> bool:
        pass

    # -------------------------
    # Relationships
    # -------------------------

    @abstractmethod
    def create_parent_relationship(
        self, data: ParentRelationshipDTO
    ) -> ParentRelationshipResponseDTO:
        pass

    @abstractmethod
    def delete_parent_relationship(self, data: DeleteRelationshipDTO) -> bool:
        pass

    @abstractmethod
    def create_spouse_relationship(
        self, data: SpouseRelationshipDTO
    ) -> SpouseRelationshipResponseDTO:
        pass

    @abstractmethod
    def delete_spouse_relationship(self, data: DeleteSpouseRelationshipDTO) -> bool:
        pass
