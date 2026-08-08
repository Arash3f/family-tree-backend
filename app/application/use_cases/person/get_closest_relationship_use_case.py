from uuid import UUID

from app.domain.exceptions.person_exceptions import PersonNotFoundException
from app.domain.repositories.family_tree_repository import FamilyTreeRepository
from app.domain.shared.dto.family_tree_dto import PersonIdDTO, RelationshipPathDTO


class GetClosestRelationshipUseCase:
    def __init__(self, family_tree_repo: FamilyTreeRepository):
        self.family_tree_repo = family_tree_repo

    def execute(self, from_person_id: UUID, to_person_id: UUID) -> RelationshipPathDTO:
        if not self.family_tree_repo.person_exists(PersonIdDTO(id=from_person_id)):
            raise PersonNotFoundException(
                detail=[f"person {from_person_id} not found in graph"]
            )

        if not self.family_tree_repo.person_exists(PersonIdDTO(id=to_person_id)):
            raise PersonNotFoundException(
                detail=[f"person {to_person_id} not found in graph"]
            )

        return self.family_tree_repo.find_shortest_relationship_path(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
        )
