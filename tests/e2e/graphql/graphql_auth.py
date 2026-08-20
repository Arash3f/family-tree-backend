import pytest_asyncio
from family_tree_graphql_client import FamilyTreeGraphQLClient
from httpx import ASGITransport, AsyncClient

from app.core.config import settings


def gql_client_with_headers(
    asgi_transport: ASGITransport, headers: dict[str, str] | None = None
) -> FamilyTreeGraphQLClient:
    """Build a type-safe GraphQL client authenticated with pre-obtained headers.

    Used for actors created via `create_authenticated_user` (custom
    permissions), which log in over REST and only hand back headers.
    """
    async_httpx = AsyncClient(
        transport=asgi_transport, base_url="http://testserver", headers=headers or {}
    )
    return FamilyTreeGraphQLClient(
        url="http://testserver/graphql", http_client=async_httpx
    )


async def _login(
    asgi_transport: ASGITransport, username: str, password: str
) -> FamilyTreeGraphQLClient:
    anonymous = FamilyTreeGraphQLClient(
        url="http://testserver/graphql",
        http_client=AsyncClient(transport=asgi_transport, base_url="http://testserver"),
    )
    response = await anonymous.login(username=username, password=password)
    await anonymous.http_client.aclose()

    return gql_client_with_headers(
        asgi_transport,
        headers={"Authorization": f"Bearer {response.login.access_token}"},
    )


@pytest_asyncio.fixture
async def gql_client(asgi_transport: ASGITransport) -> FamilyTreeGraphQLClient:
    async_httpx = AsyncClient(transport=asgi_transport, base_url="http://testserver")
    unauthenticated = FamilyTreeGraphQLClient(
        url="http://testserver/graphql", http_client=async_httpx
    )
    yield unauthenticated
    await unauthenticated.http_client.aclose()


@pytest_asyncio.fixture
async def admin_gql_client(asgi_transport: ASGITransport) -> FamilyTreeGraphQLClient:
    authenticated = await _login(
        asgi_transport, settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD
    )
    yield authenticated
    await authenticated.http_client.aclose()


@pytest_asyncio.fixture
async def member_gql_client(asgi_transport: ASGITransport) -> FamilyTreeGraphQLClient:
    authenticated = await _login(asgi_transport, "member_user", "member_user")
    yield authenticated
    await authenticated.http_client.aclose()
