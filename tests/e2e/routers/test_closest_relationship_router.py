import json
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.persons.get_closest_relationship_family_trees_tree_id_persons_from_person_id_relation_to_person_id_get import (  # noqa: E501
    asyncio_detailed as get_closest_relationship,
)
from family_tree_api_client.models.closest_relationship_response import (
    ClosestRelationshipResponse,
)

from app.domain.entities.person import Gender, Person
from app.domain.shared.dto.family_tree_dto import RelationshipPathDTO
from app.main import app
from app.presentation.dependencies import get_neo
from app.utils.error_codes import ERROR_MESSAGES, ErrorCode
from tests.e2e.auth_headers import admin_client as admin_client
from tests.e2e.auth_headers import member_client as member_client
from tests.helpers.uow import TreeUnitOfWork


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
async def test_closest_relationship_permission_denied(
    tree_id,
    member_client: AuthenticatedClient,
    mock_neo,  # noqa: F811
):
    from_id, to_id = uuid4(), uuid4()
    resp = await get_closest_relationship(
        client=member_client,
        tree_id=tree_id,
        from_person_id=from_id,
        to_person_id=to_id,
    )
    assert resp.status_code == 403
    body = json.loads(resp.content)
    assert body["error_code"] == 1301
    assert body["message"] == ERROR_MESSAGES["en"][ErrorCode.PERMISSION_DENIED]
    mock_neo.find_shortest_relationship_path.assert_not_called()


@pytest.mark.asyncio
async def test_closest_relationship_unauthenticated(client: Client, tree_id, mock_neo):
    resp = await get_closest_relationship(
        client=client,
        tree_id=tree_id,
        from_person_id=uuid4(),
        to_person_id=uuid4(),
    )
    assert resp.status_code == 401
    assert json.loads(resp.content)["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_closest_relationship_success(
    tree_id,
    admin_client: AuthenticatedClient,
    uow: TreeUnitOfWork,
    mock_neo,  # noqa: F811
):
    # The endpoint resolves both persons in Postgres before querying the graph.
    from_person = await uow.persons.create(
        Person(id=None, tree_id=tree_id, name="From", gender=Gender.MALE)
    )
    to_person = await uow.persons.create(
        Person(id=None, tree_id=tree_id, name="To", gender=Gender.FEMALE)
    )
    await uow.commit()

    from_id, to_id, mid = from_person.safe_id, to_person.safe_id, uuid4()
    mock_neo.person_exists.return_value = True
    mock_neo.find_shortest_relationship_path.return_value = RelationshipPathDTO(
        from_person_id=from_id,
        to_person_id=to_id,
        found=True,
        distance=2,
        path_person_ids=[from_id, mid, to_id],
        relationship_types=["PARENT_OF", "PARENT_OF"],
    )

    resp = await get_closest_relationship(
        client=admin_client,
        tree_id=tree_id,
        from_person_id=from_id,
        to_person_id=to_id,
    )
    assert resp.status_code == 200, resp.content
    assert isinstance(resp.parsed, ClosestRelationshipResponse)
    body = resp.parsed
    assert body.found is True
    assert body.distance == 2
    assert body.from_person_id == from_id
    assert body.to_person_id == to_id
    assert body.path_person_ids == [from_id, mid, to_id]
    assert body.relationship_types == ["PARENT_OF", "PARENT_OF"]


@pytest.mark.asyncio
async def test_closest_relationship_person_missing(
    tree_id,
    admin_client: AuthenticatedClient,
    mock_neo,  # noqa: F811
):
    from_id, to_id = uuid4(), uuid4()
    mock_neo.person_exists.return_value = False

    resp = await get_closest_relationship(
        client=admin_client,
        tree_id=tree_id,
        from_person_id=from_id,
        to_person_id=to_id,
    )
    assert resp.status_code == 404
    assert json.loads(resp.content)["error_code"] == int(ErrorCode.PERSON_NOT_FOUND)
