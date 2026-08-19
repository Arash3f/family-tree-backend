import pytest_asyncio
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.auth.login_auth_login_post import (
    asyncio_detailed as login,
)
from family_tree_api_client.models.body_login_auth_login_post import (
    BodyLoginAuthLoginPost,
)
from family_tree_api_client.models.login_response import LoginResponse
from httpx import ASGITransport, AsyncClient

from app.core.config import settings


async def _login(
    client: Client, asgi_transport: ASGITransport, username: str, password: str
) -> AuthenticatedClient:
    response = await login(
        client=client,
        body=BodyLoginAuthLoginPost(username=username, password=password),
    )

    assert response.status_code == 200, response.content

    assert isinstance(response.parsed, LoginResponse)
    token = response.parsed.access_token

    async_httpx = AsyncClient(
        transport=asgi_transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {token}"},
    )
    authenticated = AuthenticatedClient(base_url="http://testserver", token=token)
    authenticated.set_async_httpx_client(async_httpx)
    return authenticated


@pytest_asyncio.fixture
async def admin_client(
    client: Client, asgi_transport: ASGITransport
) -> AuthenticatedClient:
    authenticated = await _login(
        client, asgi_transport, settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD
    )
    yield authenticated
    await authenticated.get_async_httpx_client().aclose()


@pytest_asyncio.fixture
async def member_client(
    client: Client, asgi_transport: ASGITransport
) -> AuthenticatedClient:
    authenticated = await _login(client, asgi_transport, "member_user", "member_user")
    yield authenticated
    await authenticated.get_async_httpx_client().aclose()
