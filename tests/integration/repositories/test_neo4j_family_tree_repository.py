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
async def neo_repo():
    try:
        result = await neo4j_client.execute_read("RETURN 1 AS ok", params={})
        if not result:
            pytest.skip("Neo4j not available")
    except Exception:
        pytest.skip("Neo4j not available")

    return Neo4jFamilyTreeRepository()


@pytest.mark.asyncio
async def test_neo4j_upsert_parent_and_shortest_path(neo_repo):
    tree_id = uuid4()
    father_id = uuid4()
    child_id = uuid4()

    await neo_repo.upsert_person(
        PersonUpsertDTO(
            id=father_id,
            tree_id=tree_id,
            full_name="Father",
            gender="MALE",
            birth_date=date(1970, 1, 1),
        )
    )
    await neo_repo.upsert_person(
        PersonUpsertDTO(
            id=child_id,
            tree_id=tree_id,
            full_name="Child",
            gender="MALE",
            birth_date=date(2000, 1, 1),
        )
    )
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=father_id, child_id=child_id)
    )

    path = await neo_repo.find_shortest_relationship_path(
        father_id, child_id, tree_id=tree_id
    )

    assert path.found is True
    assert path.distance == 1
    assert path.relationship_types == ["PARENT_OF"]

    await neo_repo.delete_person(PersonIdDTO(id=child_id))
    await neo_repo.delete_person(PersonIdDTO(id=father_id))


async def _upsert(neo_repo, person_id, tree_id, name):
    await neo_repo.upsert_person(
        PersonUpsertDTO(
            id=person_id,
            tree_id=tree_id,
            full_name=name,
            gender="MALE",
            birth_date=date(1970, 1, 1),
        )
    )


@pytest.mark.asyncio
async def test_shortest_path_ignores_people_from_another_tree(neo_repo):
    """Two related people in a foreign tree must not resolve for this tree."""
    tree_a = uuid4()
    tree_b = uuid4()
    outsider_parent = uuid4()
    outsider_child = uuid4()

    await _upsert(neo_repo, outsider_parent, tree_b, "Foreign Parent")
    await _upsert(neo_repo, outsider_child, tree_b, "Foreign Child")
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=outsider_parent, child_id=outsider_child)
    )

    try:
        path = await neo_repo.find_shortest_relationship_path(
            outsider_parent, outsider_child, tree_id=tree_a
        )
        assert path.found is False
    finally:
        await neo_repo.delete_person(PersonIdDTO(id=outsider_child))
        await neo_repo.delete_person(PersonIdDTO(id=outsider_parent))


@pytest.mark.asyncio
async def test_shortest_path_does_not_route_through_a_foreign_tree(neo_repo):
    """A person shared with another tree must not bridge two unrelated people."""
    tree_a = uuid4()
    tree_b = uuid4()
    left = uuid4()
    bridge = uuid4()
    right = uuid4()

    await _upsert(neo_repo, left, tree_a, "Left")
    await _upsert(neo_repo, bridge, tree_b, "Bridge")
    await _upsert(neo_repo, right, tree_a, "Right")
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=left, child_id=bridge)
    )
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=bridge, child_id=right)
    )

    try:
        path = await neo_repo.find_shortest_relationship_path(
            left, right, tree_id=tree_a
        )
        assert path.found is False

        unscoped = await neo_repo.find_shortest_relationship_path(
            left, right, tree_id=None
        )
        assert unscoped.found is True
        assert unscoped.distance == 2
    finally:
        for person_id in (left, bridge, right):
            await neo_repo.delete_person(PersonIdDTO(id=person_id))
