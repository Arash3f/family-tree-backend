import pytest
from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.auth.login_auth_login_post import (
    asyncio_detailed as login,
)
from family_tree_api_client.api.auth.logout_auth_logout_post import (
    asyncio_detailed as logout,
)
from family_tree_api_client.api.auth.me_auth_me_get import asyncio_detailed as me
from family_tree_api_client.api.auth.refresh_auth_refresh_post import (
    asyncio_detailed as refresh,
)
from family_tree_api_client.models.body_login_auth_login_post import (
    BodyLoginAuthLoginPost,
)
from family_tree_api_client.models.login_response import LoginResponse
from family_tree_api_client.models.me_response import MeResponse
from family_tree_api_client.models.refresh_token_request import RefreshTokenRequest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from tests.e2e.auth_headers import admin_client as admin_client
from tests.e2e.auth_headers import member_client as member_client


@pytest.mark.asyncio
async def test_login_success(client: Client):
    response = await login(
        client=client,
        body=BodyLoginAuthLoginPost(
            username=settings.ADMIN_USERNAME,
            password=settings.ADMIN_PASSWORD,
        ),
    )

    assert response.status_code == 200
    assert isinstance(response.parsed, LoginResponse)
    assert response.parsed.access_token
    assert response.parsed.refresh_token


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: Client):
    response = await login(
        client=client,
        body=BodyLoginAuthLoginPost(
            username=settings.ADMIN_USERNAME, password="wrong-password"
        ),
    )

    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_me_requires_access_token(admin_client: AuthenticatedClient):
    response = await me(client=admin_client)
    assert response.status_code == 200
    assert isinstance(response.parsed, MeResponse)
    assert response.parsed.username == settings.ADMIN_USERNAME
    assert response.parsed.permissions is not None
    assert isinstance(response.parsed.permissions, list)
    assert "user_read" in response.parsed.permissions


@pytest.mark.asyncio
async def test_me_rejects_refresh_token(client: Client, asgi_transport: ASGITransport):
    login_response = await login(
        client=client,
        body=BodyLoginAuthLoginPost(
            username=settings.ADMIN_USERNAME,
            password=settings.ADMIN_PASSWORD,
        ),
    )
    assert isinstance(login_response.parsed, LoginResponse)
    refresh_token = login_response.parsed.refresh_token

    async_httpx = AsyncClient(
        transport=asgi_transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    refresh_client = AuthenticatedClient(
        base_url="http://testserver", token=refresh_token
    )
    refresh_client.set_async_httpx_client(async_httpx)

    response = await me(client=refresh_client)

    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_refresh_token_success(client: Client):
    login_response = await login(
        client=client,
        body=BodyLoginAuthLoginPost(
            username=settings.ADMIN_USERNAME,
            password=settings.ADMIN_PASSWORD,
        ),
    )
    assert isinstance(login_response.parsed, LoginResponse)
    refresh_token = login_response.parsed.refresh_token

    response = await refresh(
        client=client, body=RefreshTokenRequest(refresh_token=refresh_token)
    )

    assert response.status_code == 200
    assert isinstance(response.parsed, LoginResponse)
    assert response.parsed.access_token
    assert response.parsed.refresh_token
    assert response.parsed.refresh_token != refresh_token


@pytest.mark.asyncio
async def test_refresh_old_token_rejected_after_rotation(client: Client):
    login_response = await login(
        client=client,
        body=BodyLoginAuthLoginPost(
            username=settings.ADMIN_USERNAME,
            password=settings.ADMIN_PASSWORD,
        ),
    )
    assert isinstance(login_response.parsed, LoginResponse)
    old_refresh = login_response.parsed.refresh_token

    first = await refresh(
        client=client, body=RefreshTokenRequest(refresh_token=old_refresh)
    )
    assert first.status_code == 200

    reused = await refresh(
        client=client, body=RefreshTokenRequest(refresh_token=old_refresh)
    )
    assert reused.status_code in (401, 422)


@pytest.mark.asyncio
async def test_refresh_rejects_access_token(admin_client: AuthenticatedClient):
    access_token = admin_client.token

    response = await refresh(
        client=admin_client, body=RefreshTokenRequest(refresh_token=access_token)
    )

    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_logout_revokes_session(admin_client: AuthenticatedClient):
    me_before = await me(client=admin_client)
    assert me_before.status_code == 200

    logout_response = await logout(client=admin_client)
    assert logout_response.status_code == 200

    me_after = await me(client=admin_client)
    assert me_after.status_code in (401, 422)


@pytest.mark.asyncio
async def test_member_can_login(member_client: AuthenticatedClient):
    assert member_client.token
