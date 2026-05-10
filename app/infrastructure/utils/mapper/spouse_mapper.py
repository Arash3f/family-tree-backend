from typing import Sequence

from neo4j import Record

from app.domain.shared.dto.family_tree_dto import (
    PersonCompleteBaseDTO,
    SpouseRelationshipResponseDTO,
)
from app.infrastructure.utils.neo4j_normalizer import normalize_neo4j_value


def map_neo4j_spouse(record: Record) -> SpouseRelationshipResponseDTO:
    person_1_node = record.get("a")
    person_2_node = record.get("b")

    if person_1_node is None or person_2_node is None:
        raise ValueError("Record does not contain required spouse fields")

    person_1_props = {
        k: normalize_neo4j_value(v) for k, v in dict(person_1_node).items()
    }
    person_1 = PersonCompleteBaseDTO(**person_1_props)
    person_2_props = {
        k: normalize_neo4j_value(v) for k, v in dict(person_2_node).items()
    }
    person_2 = PersonCompleteBaseDTO(**person_2_props)

    return SpouseRelationshipResponseDTO(person_1=person_1, person_2=person_2)


def map_neo4j_spouses(records: Sequence[Record]) -> list[SpouseRelationshipResponseDTO]:
    return [map_neo4j_spouse(r) for r in records]
