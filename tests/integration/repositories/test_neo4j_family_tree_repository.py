from datetime import date
from uuid import uuid4

import pytest

from app.domain.shared.dto.family_tree_dto import (
    ParentRelationshipDTO,
    PersonIdDTO,
    PersonUpsertDTO,
)
from app.infrastructure.database.neo4j.neo4j import neo4j_client
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)


@pytest.fixture
def neo_repo():
    try:
        result = neo4j_client.execute_read("RETURN 1 AS ok", params={})
        if not result:
            pytest.skip("Neo4j not available")
    except Exception:
        pytest.skip("Neo4j not available")

    return Neo4jFamilyTreeRepository()


def test_neo4j_upsert_parent_and_shortest_path(neo_repo):
    tree_id = uuid4()
    father_id = uuid4()
    child_id = uuid4()

    neo_repo.upsert_person(
        PersonUpsertDTO(
            id=father_id,
            tree_id=tree_id,
            full_name="Father",
            gender="MALE",
            birth_date=date(1970, 1, 1),
        )
    )
    neo_repo.upsert_person(
        PersonUpsertDTO(
            id=child_id,
            tree_id=tree_id,
            full_name="Child",
            gender="MALE",
            birth_date=date(2000, 1, 1),
        )
    )
    neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=father_id, child_id=child_id)
    )

    path = neo_repo.find_shortest_relationship_path(
        father_id, child_id, tree_id=tree_id
    )

    assert path.found is True
    assert path.distance == 1
    assert path.relationship_types == ["PARENT_OF"]

    neo_repo.delete_person(PersonIdDTO(id=child_id))
    neo_repo.delete_person(PersonIdDTO(id=father_id))
