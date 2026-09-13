from datetime import date
from uuid import uuid4

import pytest

from app.domain.shared.dto.family_tree_dto import (
    ParentRelationshipDTO,
    PersonIdDTO,
    PersonUpsertDTO,
    SpouseRelationshipDTO,
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


@pytest.mark.asyncio
async def test_male_only_path_skips_female_intermediates(neo_repo):
    """With male_only, a mother bridge is rejected; a father bridge is kept."""
    tree_id = uuid4()
    father_id = uuid4()
    mother_id = uuid4()
    child_a = uuid4()
    child_b = uuid4()

    async def upsert(person_id, name, gender):
        await neo_repo.upsert_person(
            PersonUpsertDTO(
                id=person_id,
                tree_id=tree_id,
                full_name=name,
                gender=gender,
                birth_date=date(1970, 1, 1),
            )
        )

    await upsert(father_id, "Father", "MALE")
    await upsert(mother_id, "Mother", "FEMALE")
    await upsert(child_a, "Child A", "MALE")
    await upsert(child_b, "Child B", "MALE")
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=mother_id, child_id=child_a)
    )
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=mother_id, child_id=child_b)
    )
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=father_id, child_id=child_a)
    )
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=father_id, child_id=child_b)
    )

    try:
        via_anyone = await neo_repo.find_shortest_relationship_path(
            child_a, child_b, tree_id=tree_id
        )
        assert via_anyone.found is True
        assert via_anyone.distance == 2

        via_males = await neo_repo.find_shortest_relationship_path(
            child_a, child_b, tree_id=tree_id, male_only=True
        )
        assert via_males.found is True
        assert via_males.distance == 2
        assert via_males.path_person_ids == [child_a, father_id, child_b]

        await neo_repo.delete_person(PersonIdDTO(id=father_id))
        only_mother = await neo_repo.find_shortest_relationship_path(
            child_a, child_b, tree_id=tree_id, male_only=True
        )
        assert only_mother.found is False
    finally:
        for person_id in (child_a, child_b, father_id, mother_id):
            await neo_repo.delete_person(PersonIdDTO(id=person_id))


@pytest.mark.asyncio
async def test_diverse_paths_keep_both_parent_routes(neo_repo):
    """Two full siblings have two parent routes; both should come back."""
    tree_id = uuid4()
    father_id = uuid4()
    mother_id = uuid4()
    child_a = uuid4()
    child_b = uuid4()

    await _upsert(neo_repo, father_id, tree_id, "Father")
    await _upsert(neo_repo, mother_id, tree_id, "Mother")
    await _upsert(neo_repo, child_a, tree_id, "Child A")
    await _upsert(neo_repo, child_b, tree_id, "Child B")
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=father_id, child_id=child_a)
    )
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=father_id, child_id=child_b)
    )
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=mother_id, child_id=child_a)
    )
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=mother_id, child_id=child_b)
    )

    try:
        result = await neo_repo.find_diverse_relationship_paths(
            child_a, child_b, tree_id=tree_id
        )
        assert result.found is True
        assert result.distance == 2
        assert len(result.paths) == 2
        intermediates = {frozenset(item.path_person_ids[1:-1]) for item in result.paths}
        assert frozenset([father_id]) in intermediates
        assert frozenset([mother_id]) in intermediates
    finally:
        for person_id in (child_a, child_b, father_id, mother_id):
            await neo_repo.delete_person(PersonIdDTO(id=person_id))


@pytest.mark.asyncio
async def test_diverse_paths_include_blood_and_marriage(neo_repo):
    """Spouses sharing a child: marriage is shortest; alt goes via the child."""
    tree_id = uuid4()
    spouse_a = uuid4()
    spouse_b = uuid4()
    child_id = uuid4()

    await _upsert(neo_repo, spouse_a, tree_id, "Spouse A")
    await _upsert(neo_repo, spouse_b, tree_id, "Spouse B")
    await _upsert(neo_repo, child_id, tree_id, "Child")
    await neo_repo.create_spouse_relationship(
        SpouseRelationshipDTO(person_id_1=spouse_a, person_id_2=spouse_b)
    )
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=spouse_a, child_id=child_id)
    )
    await neo_repo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=spouse_b, child_id=child_id)
    )

    try:
        result = await neo_repo.find_diverse_relationship_paths(
            spouse_a, spouse_b, tree_id=tree_id
        )
        assert result.found is True
        assert result.distance == 1
        assert result.relationship_types == ["SPOUSE_OF"]
        assert len(result.paths) == 2
        via_child = next(item for item in result.paths if item.distance == 2)
        assert child_id in via_child.path_person_ids
    finally:
        for person_id in (child_id, spouse_a, spouse_b):
            await neo_repo.delete_person(PersonIdDTO(id=person_id))


@pytest.mark.asyncio
async def test_diverse_paths_do_not_route_through_a_foreign_tree(neo_repo):
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
        result = await neo_repo.find_diverse_relationship_paths(
            left, right, tree_id=tree_a
        )
        assert result.found is False
        assert result.paths == []
    finally:
        for person_id in (left, bridge, right):
            await neo_repo.delete_person(PersonIdDTO(id=person_id))
