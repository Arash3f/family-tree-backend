from typing import Sequence

from neo4j import Record

from app.domain.shared.dto.family_tree_dto import PersonResponseDTO
from app.utils.neo4j_normalizer import normalize_neo4j_value


def map_neo4j_person(record: Record, key: str = "p") -> PersonResponseDTO:
    node = record.get(key)
    if node is None:
        raise ValueError(f"No node found under key: {key}")

    props = {k: normalize_neo4j_value(v) for k, v in dict(node).items()}
    return PersonResponseDTO(**props)


def map_neo4j_people(
    records: Sequence[Record], key: str = "p"
) -> list[PersonResponseDTO]:
    return [map_neo4j_person(record, key) for record in records]
