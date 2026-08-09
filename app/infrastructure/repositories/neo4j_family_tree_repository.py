from uuid import UUID

from pydantic import BaseModel

from app.domain.repositories.family_tree_repository import FamilyTreeRepository
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
from app.infrastructure.database.neo4j import neo4j_queries as q
from app.infrastructure.database.neo4j.neo4j import neo4j_client
from app.infrastructure.utils.mapper.parent_mapper import map_neo4j_parent
from app.infrastructure.utils.mapper.person_mapper import map_neo4j_person
from app.infrastructure.utils.mapper.spouse_mapper import map_neo4j_spouse


class _PathParams(BaseModel):
    from_id: UUID
    to_id: UUID
    tree_id: UUID | None = None


class _PersonExistsParams(BaseModel):
    id: UUID
    tree_id: UUID | None = None


class Neo4jFamilyTreeRepository(FamilyTreeRepository):
    # ============================
    # PERSON
    # ============================

    def upsert_person(self, data: PersonUpsertDTO) -> PersonResponseDTO:
        records = neo4j_client.execute_write(query=q.UPSERT_PERSON, params=data)

        return map_neo4j_person(records[0])

    def delete_person(self, data: PersonIdDTO) -> bool:
        records = neo4j_client.execute_write(query=q.DELETE_PERSON, params=data)
        if not records:
            return False

        return bool(records[0]["deleted"])

    def get_person(self, data: PersonIdDTO) -> PersonResponseDTO:
        result = neo4j_client.execute_read(query=q.GET_PERSON, params=data)
        return map_neo4j_person(result[0])

    def person_exists(
        self, data: PersonIdDTO, tree_id: UUID | None = None
    ) -> bool:
        result = neo4j_client.execute_read(
            query=q.PERSON_EXISTS,
            params=_PersonExistsParams(
                id=data.id, tree_id=tree_id if tree_id is not None else data.tree_id
            ),
        )
        return len(result) > 0

    # ============================
    # RELATIONSHIPS
    # ============================

    def create_parent_relationship(
        self, data: ParentRelationshipDTO
    ) -> ParentRelationshipResponseDTO:
        records = neo4j_client.execute_write(
            query=q.CREATE_PARENT_REL,
            params=data,
        )
        return map_neo4j_parent(records[0])

    def delete_parent_relationship(self, data: DeleteRelationshipDTO) -> bool:
        records = neo4j_client.execute_write(
            query=q.DELETE_PARENT_REL,
            params=data,
        )

        if not records:
            return False

        return bool(records[0]["deleted"])

    def create_spouse_relationship(
        self, data: SpouseRelationshipDTO
    ) -> SpouseRelationshipResponseDTO:
        records = neo4j_client.execute_write(
            query=q.CREATE_SPOUSE_REL,
            params=data,
        )
        return map_neo4j_spouse(records[0])

    def delete_spouse_relationship(self, data: DeleteSpouseRelationshipDTO) -> bool:
        records = neo4j_client.execute_write(
            query=q.DELETE_SPOUSE_REL,
            params=data,
        )

        if not records:
            return False

        return bool(records[0]["deleted"])

    def find_shortest_relationship_path(
        self,
        from_person_id: UUID,
        to_person_id: UUID,
        tree_id: UUID | None = None,
    ) -> RelationshipPathDTO:
        records = neo4j_client.execute_read(
            query=q.SHORTEST_RELATIONSHIP_PATH,
            params=_PathParams(
                from_id=from_person_id, to_id=to_person_id, tree_id=tree_id
            ),
        )

        if not records:
            return RelationshipPathDTO(
                from_person_id=from_person_id,
                to_person_id=to_person_id,
                found=False,
            )

        row = records[0]
        distance = row.get("distance")
        person_ids = [UUID(str(pid)) for pid in (row.get("person_ids") or [])]

        return RelationshipPathDTO(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            found=distance is not None,
            distance=distance,
            path_person_ids=person_ids,
            relationship_types=list(row.get("relationship_types") or []),
        )
