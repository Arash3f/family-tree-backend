from typing import Sequence

from neo4j import Record

from app.domain.shared.dto.family_tree_dto import (
    ParentRelationshipResponseDTO,
    PersonCompleteBaseDTO,
)
from app.infrastructure.utils.neo4j_normalizer import normalize_neo4j_value


def map_neo4j_parent(record: Record) -> ParentRelationshipResponseDTO:
    parent_node = record["parent"]
    child_node = record["child"]

    parent_props = {k: normalize_neo4j_value(v) for k, v in dict(parent_node).items()}
    parent = PersonCompleteBaseDTO(**parent_props)
    child_props = {k: normalize_neo4j_value(v) for k, v in dict(child_node).items()}
    child = PersonCompleteBaseDTO(**child_props)

    return ParentRelationshipResponseDTO(parent=parent, child=child)


def map_neo4j_parents(records: Sequence[Record]) -> list[ParentRelationshipResponseDTO]:
    return [map_neo4j_parent(r) for r in records]
