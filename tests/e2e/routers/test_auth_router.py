import pytest

from app.core.config import settings
from tests.e2e.auth_headers import admin_headers as admin_headers
from tests.e2e.auth_headers import member_headers as member_headers


@pytest.mark.asyncio
async def test_login_success(client):
    response = await client.post(
        "/auth/login",
        data={
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    response = await client.post(
        "/auth/login",
        data={"username": settings.ADMIN_USERNAME, "password": "wrong-password"},
    )

    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_me_requires_access_token(client, admin_headers):  # noqa: F811
    response = await client.get("/auth/me", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == settings.ADMIN_USERNAME


@pytest.mark.asyncio
async def test_me_rejects_refresh_token(client):
    login = await client.post(
        "/auth/login",
        data={
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_refresh_token_success(client):
    login = await client.post(
        "/auth/login",
        data={
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_old_token_rejected_after_rotation(client):
    login = await client.post(
        "/auth/login",
        data={
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    old_refresh = login.json()["refresh_token"]

    first = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert first.status_code == 200

    reused = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code in (401, 422)


@pytest.mark.asyncio
async def test_refresh_rejects_access_token(client, admin_headers):  # noqa: F811
    access_token = admin_headers["Authorization"].removeprefix("Bearer ")

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_logout_revokes_session(client, admin_headers):  # noqa: F811
    me_before = await client.get("/auth/me", headers=admin_headers)
    assert me_before.status_code == 200

    logout = await client.post("/auth/logout", headers=admin_headers)
    assert logout.status_code == 200

    me_after = await client.get("/auth/me", headers=admin_headers)
    assert me_after.status_code in (401, 422)


@pytest.mark.asyncio
async def test_member_can_login(client, member_headers):  # noqa: F811
    assert "Authorization" in member_headers
