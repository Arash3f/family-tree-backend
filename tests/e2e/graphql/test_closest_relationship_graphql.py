from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from app.domain.entities.person import Gender, Person
from app.domain.shared.dto.family_tree_dto import RelationshipPathDTO
from app.main import app
from app.presentation.rest.utils.dependencies import get_neo
from app.utils.error_codes import ErrorCode
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.e2e.auth_headers import member_headers as member_headers
from tests.e2e.graphql.test_person_graphql import gql
from tests.helpers.uow import TreeUnitOfWork

CLOSEST = """
query ClosestRelationship($treeId: UUID!, $fromId: UUID!, $toId: UUID!) {
  closestRelationship(treeId: $treeId, fromPersonId: $fromId, toPersonId: $toId) {
    fromPersonId
    toPersonId
    found
    distance
    pathPersonIds
    relationshipTypes
  }
}
"""


@pytest.fixture
def mock_neo():
    repo = MagicMock()
    original = app.dependency_overrides.get(get_neo)
    app.dependency_overrides[get_neo] = lambda: repo
    yield repo
    if original is None:
        app.dependency_overrides.pop(get_neo, None)
    else:
        app.dependency_overrides[get_neo] = original


@pytest.mark.asyncio
async def test_graphql_closest_relationship_permission_denied(
    client,
    tree_id,
    member_headers,
    mock_neo,  # noqa: F811
):
    resp = await gql(
        client,
        CLOSEST,
        {
            "treeId": str(tree_id),
            "fromId": str(uuid4()),
            "toId": str(uuid4()),
        },
        headers=member_headers,
    )
    assert resp.status_code == 200
    errors = resp.json()["errors"]
    assert errors[0]["extensions"]["error_code"] == int(ErrorCode.PERMISSION_DENIED)
    mock_neo.find_shortest_relationship_path.assert_not_called()


@pytest.mark.asyncio
async def test_graphql_closest_relationship_success(
    client,
    tree_id,
    admin_headers,
    uow: TreeUnitOfWork,
    mock_neo,  # noqa: F811
):
    # The resolver resolves the persons in Postgres before touching the graph.
    from_person = await uow.persons.create(
        Person(id=None, tree_id=tree_id, name="From", gender=Gender.MALE)
    )
    to_person = await uow.persons.create(
        Person(id=None, tree_id=tree_id, name="To", gender=Gender.FEMALE)
    )
    await uow.commit()

    from_id, to_id = from_person.safe_id, to_person.safe_id
    mock_neo.person_exists.return_value = True
    mock_neo.find_shortest_relationship_path.return_value = RelationshipPathDTO(
        from_person_id=from_id,
        to_person_id=to_id,
        found=True,
        distance=1,
        path_person_ids=[from_id, to_id],
        relationship_types=["SPOUSE_OF"],
    )

    resp = await gql(
        client,
        CLOSEST,
        {
            "treeId": str(tree_id),
            "fromId": str(from_id),
            "toId": str(to_id),
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert "errors" not in payload, payload
    data = payload["data"]["closestRelationship"]
    assert data["found"] is True
    assert data["distance"] == 1
    assert data["fromPersonId"] == str(from_id)
    assert data["toPersonId"] == str(to_id)
    assert data["relationshipTypes"] == ["SPOUSE_OF"]
