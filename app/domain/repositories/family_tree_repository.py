from abc import ABC, abstractmethod

from uuid import UUID

from app.domain.shared.dto.family_tree_dto import (
    DeleteRelationshipDTO,
    DeleteSpouseRelationshipDTO,
    ParentRelationshipDTO,
    ParentRelationshipResponseDTO,
    PersonIdDTO,
    PersonResponseDTO,
    PersonUpsertDTO,
    RelationshipPathDTO,
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
    def person_exists(self, data: PersonIdDTO, tree_id: UUID | None = None) -> bool:
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

    @abstractmethod
    def find_shortest_relationship_path(
        self,
        from_person_id: UUID,
        to_person_id: UUID,
        tree_id: UUID | None = None,
    ) -> RelationshipPathDTO:
        pass
