from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from family_tree_graphql_client import FamilyTreeGraphQLClient
from family_tree_graphql_client.exceptions import GraphQLClientGraphQLMultiError

from app.domain.entities.person import Gender, Person
from app.domain.shared.dto.family_tree_dto import RelationshipPathDTO
from app.main import app
from app.presentation.dependencies import get_neo
from app.utils.error_codes import ErrorCode
from tests.e2e.graphql.graphql_auth import admin_gql_client as admin_gql_client
from tests.e2e.graphql.graphql_auth import member_gql_client as member_gql_client
from tests.helpers.uow import TreeUnitOfWork


@pytest.fixture
def mock_neo():
    repo = AsyncMock()
    original = app.dependency_overrides.get(get_neo)
    app.dependency_overrides[get_neo] = lambda: repo
    yield repo
    if original is None:
        app.dependency_overrides.pop(get_neo, None)
    else:
        app.dependency_overrides[get_neo] = original


@pytest.mark.asyncio
async def test_graphql_closest_relationship_permission_denied(
    tree_id,
    member_gql_client: FamilyTreeGraphQLClient,
    mock_neo,  # noqa: F811
):
    with pytest.raises(GraphQLClientGraphQLMultiError) as exc_info:
        await member_gql_client.closest_relationship(
            tree_id=tree_id, from_id=uuid4(), to_id=uuid4()
        )

    error = exc_info.value.errors[0]
    assert error.extensions["error_code"] == int(ErrorCode.TREE_MEMBERSHIP_DENIED)
    mock_neo.find_shortest_relationship_path.assert_not_called()


@pytest.mark.asyncio
async def test_graphql_closest_relationship_success(
    tree_id,
    admin_gql_client: FamilyTreeGraphQLClient,
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

    resp = await admin_gql_client.closest_relationship(
        tree_id=tree_id, from_id=from_id, to_id=to_id
    )
    data = resp.closest_relationship
    assert data.found is True
    assert data.distance == 1
    assert str(data.from_person_id) == str(from_id)
    assert str(data.to_person_id) == str(to_id)
    assert data.relationship_types == ["SPOUSE_OF"]
