from datetime import date

import pytest

from app.domain.entities.person import Gender, Person
from app.domain.shared.dto.family_tree_dto import (
    ParentRelationshipDTO,
    PersonIdDTO,
    PersonUpsertDTO,
)
from app.infrastructure.database.neo4j.neo4j import neo4j_client
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.helpers.uow import TreeUnitOfWork


def persons_url(tree_id, suffix: str = "") -> str:
    return f"/family-trees/{tree_id}/persons{suffix}"


@pytest.fixture
async def live_neo():
    try:
        result = await neo4j_client.execute_read("RETURN 1 AS ok", params={})
        if not result:
            pytest.skip("Neo4j not available")
    except Exception:
        pytest.skip("Neo4j not available")
    return Neo4jFamilyTreeRepository()


@pytest.mark.asyncio
async def test_live_closest_relationship_rest(
    client,
    tree_id,
    admin_headers,
    uow: TreeUnitOfWork,
    live_neo,  # noqa: F811
):
    """API closest-relationship against real Neo4j (no mocked get_neo)."""
    # The endpoint validates both persons against Postgres before querying the
    # graph, so they must exist in the tree as well as in Neo4j.
    father = await uow.persons.create(
        Person(
            id=None,
            tree_id=tree_id,
            name="Live Father",
            gender=Gender.MALE,
            birth_date=date(1970, 1, 1),
        )
    )
    child = await uow.persons.create(
        Person(
            id=None,
            tree_id=tree_id,
            name="Live Child",
            gender=Gender.MALE,
            birth_date=date(2000, 1, 1),
        )
    )
    await uow.commit()

    father_id = father.safe_id
    child_id = child.safe_id

    await live_neo.upsert_person(
        PersonUpsertDTO(
            id=father_id,
            tree_id=tree_id,
            full_name="Live Father",
            gender="MALE",
            birth_date=date(1970, 1, 1),
        )
    )
    await live_neo.upsert_person(
        PersonUpsertDTO(
            id=child_id,
            tree_id=tree_id,
            full_name="Live Child",
            gender="MALE",
            birth_date=date(2000, 1, 1),
        )
    )
    await live_neo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=father_id, child_id=child_id)
    )

    try:
        resp = await client.get(
            persons_url(tree_id, f"/{father_id}/relation/{child_id}"),
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["found"] is True
        assert body["distance"] == 1
        assert body["relationship_types"] == ["PARENT_OF"]
    finally:
        await live_neo.delete_person(PersonIdDTO(id=child_id))
        await live_neo.delete_person(PersonIdDTO(id=father_id))
