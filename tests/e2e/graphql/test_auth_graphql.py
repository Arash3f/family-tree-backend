import pytest
from family_tree_graphql_client import FamilyTreeGraphQLClient
from family_tree_graphql_client.exceptions import GraphQLClientGraphQLMultiError

from app.core.config import settings
from tests.e2e.graphql.graphql_auth import admin_gql_client as admin_gql_client
from tests.e2e.graphql.graphql_auth import gql_client as gql_client
from tests.e2e.graphql.graphql_auth import member_gql_client as member_gql_client


@pytest.mark.asyncio
async def test_graphql_login_success(gql_client: FamilyTreeGraphQLClient):
    resp = await gql_client.login(
        username=settings.ADMIN_USERNAME, password=settings.ADMIN_PASSWORD
    )
    data = resp.login
    assert data.access_token
    assert data.refresh_token
    assert data.token_type == "bearer"


@pytest.mark.asyncio
async def test_graphql_login_invalid_credentials(gql_client: FamilyTreeGraphQLClient):
    with pytest.raises(GraphQLClientGraphQLMultiError) as exc_info:
        await gql_client.login(
            username=settings.ADMIN_USERNAME, password="wrong-password"
        )

    error = exc_info.value.errors[0]
    assert error.extensions["status"] in (401, 422, 400)


@pytest.mark.asyncio
async def test_graphql_me_requires_auth(gql_client: FamilyTreeGraphQLClient):
    with pytest.raises(GraphQLClientGraphQLMultiError):
        await gql_client.me()


@pytest.mark.asyncio
async def test_graphql_me_success(admin_gql_client: FamilyTreeGraphQLClient):
    resp = await admin_gql_client.me()
    assert resp.me.username == settings.ADMIN_USERNAME


@pytest.mark.asyncio
async def test_graphql_refresh_and_logout(gql_client: FamilyTreeGraphQLClient):
    login = await gql_client.login(
        username=settings.ADMIN_USERNAME, password=settings.ADMIN_PASSWORD
    )

    refreshed = await gql_client.refresh_token(token=login.login.refresh_token)
    assert refreshed.refresh_token.refresh_token != login.login.refresh_token

    gql_client.http_client.headers["Authorization"] = (
        f"Bearer {refreshed.refresh_token.access_token}"
    )
    logout = await gql_client.logout()
    assert logout.logout.result

    with pytest.raises(GraphQLClientGraphQLMultiError):
        await gql_client.me()


@pytest.mark.asyncio
async def test_graphql_member_can_login(member_gql_client: FamilyTreeGraphQLClient):
    assert "Authorization" in member_gql_client.http_client.headers
