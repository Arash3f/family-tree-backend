from typing import Sequence

from neo4j import Record

from app.domain.shared.dto.family_tree_dto import PersonResponseDTO
from app.infrastructure.utils.mapper.utils import node_to_dto


def map_neo4j_person(record: Record, key: str = "p") -> PersonResponseDTO:
    """
    Map a Neo4j record into a PersonResponseDTO.
    """

    node = record.get(key)
    if node is None:
        raise ValueError(f"No node found under key: {key}")

    return node_to_dto(node, PersonResponseDTO)


def map_neo4j_people(
    records: Sequence[Record], key: str = "p"
) -> list[PersonResponseDTO]:
    """
    Map multiple records into person DTOs.
    """

    return [map_neo4j_person(record, key) for record in records]
