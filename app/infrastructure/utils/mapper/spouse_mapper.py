from typing import Sequence

from neo4j import Record

from app.domain.shared.dto.family_tree_dto import (
    PersonCompleteBaseDTO,
    SpouseRelationshipResponseDTO,
)
from app.infrastructure.utils.mapper.utils import node_to_dto


def map_neo4j_spouse(record: Record) -> SpouseRelationshipResponseDTO:
    """
    Map a Neo4j record into a SpouseRelationshipResponseDTO.
    """

    person_1_node = record.get("a")
    person_2_node = record.get("b")

    if person_1_node is None or person_2_node is None:
        raise ValueError("Record does not contain required spouse fields")

    person_1 = node_to_dto(person_1_node, PersonCompleteBaseDTO)
    person_2 = node_to_dto(person_2_node, PersonCompleteBaseDTO)

    return SpouseRelationshipResponseDTO(
        person_1=person_1,
        person_2=person_2,
    )


def map_neo4j_spouses(records: Sequence[Record]) -> list[SpouseRelationshipResponseDTO]:
    """
    Map multiple records into person DTOs.
    """

    return [map_neo4j_spouse(r) for r in records]
