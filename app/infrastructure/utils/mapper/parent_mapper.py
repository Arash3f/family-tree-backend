from typing import Sequence

from neo4j import Record

from app.domain.shared.dto.family_tree_dto import (
    ParentRelationshipResponseDTO,
    PersonCompleteBaseDTO,
)
from app.infrastructure.utils.mapper.utils import node_to_dto


def map_neo4j_parent(record: Record) -> ParentRelationshipResponseDTO:
    """
    Map a Neo4j record into a ParentRelationshipResponseDTO.
    """

    parent = node_to_dto(record["parent"], PersonCompleteBaseDTO)
    child = node_to_dto(record["child"], PersonCompleteBaseDTO)

    return ParentRelationshipResponseDTO(
        parent=parent,
        child=child,
    )


def map_neo4j_parents(records: Sequence[Record]) -> list[ParentRelationshipResponseDTO]:
    """
    Map multiple records into person DTOs.
    """

    return [map_neo4j_parent(record) for record in records]
