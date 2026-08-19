from datetime import date

import pytest
from family_tree_api_client import AuthenticatedClient
from family_tree_api_client.api.persons.get_closest_relationship_family_trees_tree_id_persons_from_person_id_relation_to_person_id_get import (  # noqa: E501
    asyncio_detailed as get_closest_relationship,
)
from family_tree_api_client.models.closest_relationship_response import (
    ClosestRelationshipResponse,
)

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
from tests.e2e.auth_headers import admin_client as admin_client
from tests.helpers.uow import TreeUnitOfWork


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
    tree_id,
    admin_client: AuthenticatedClient,
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
        resp = await get_closest_relationship(
            tree_id=tree_id,
            from_person_id=father_id,
            to_person_id=child_id,
            client=admin_client,
        )
        assert resp.status_code == 200, resp.content
        assert isinstance(resp.parsed, ClosestRelationshipResponse)
        body = resp.parsed
        assert body.found is True
        assert body.distance == 1
        assert body.relationship_types == ["PARENT_OF"]
    finally:
        await live_neo.delete_person(PersonIdDTO(id=child_id))
        await live_neo.delete_person(PersonIdDTO(id=father_id))
