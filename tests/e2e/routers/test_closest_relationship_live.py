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
from tests.e2e.auth_headers import admin_headers as admin_headers


@pytest.fixture
def live_neo():
    try:
        result = neo4j_client.execute_read("RETURN 1 AS ok", params={})
        if not result:
            pytest.skip("Neo4j not available")
    except Exception:
        pytest.skip("Neo4j not available")
    return Neo4jFamilyTreeRepository()


@pytest.mark.asyncio
async def test_live_closest_relationship_rest(client, admin_headers, live_neo):  # noqa: F811
    """API closest-relationship against real Neo4j (no mocked get_neo)."""
    father_id = uuid4()
    child_id = uuid4()

    live_neo.upsert_person(
        PersonUpsertDTO(
            id=father_id,
            full_name="Live Father",
            gender="MALE",
            birth_date=date(1970, 1, 1),
        )
    )
    live_neo.upsert_person(
        PersonUpsertDTO(
            id=child_id,
            full_name="Live Child",
            gender="MALE",
            birth_date=date(2000, 1, 1),
        )
    )
    live_neo.create_parent_relationship(
        ParentRelationshipDTO(parent_id=father_id, child_id=child_id)
    )

    try:
        resp = await client.get(
            f"/persons/{father_id}/relation/{child_id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["found"] is True
        assert body["distance"] == 1
        assert body["relationship_types"] == ["PARENT_OF"]
    finally:
        live_neo.delete_person(PersonIdDTO(id=child_id))
        live_neo.delete_person(PersonIdDTO(id=father_id))
