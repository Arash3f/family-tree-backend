from typing import Type, TypeVar

from neo4j.graph import Node

from app.infrastructure.utils.neo4j_normalizer import normalize_neo4j_value

T = TypeVar("T")


def node_to_dict(node: Node) -> dict:
    """
    Convert a Neo4j Node into a normalized dictionary.

    Handles conversion of Neo4j-specific types
    into native Python values.
    """
    return {key: normalize_neo4j_value(value) for key, value in dict(node).items()}


def node_to_dto(node: Node, dto_class: Type[T]) -> T:
    """
    Convert a Neo4j node into a DTO instance.

    Args:
        node: Neo4j Node
        dto_class: DTO class to instantiate

    Returns:
        DTO instance
    """
    return dto_class(**node_to_dict(node))
