import pytest_asyncio
from httpx import AsyncClient

from app.core.config import settings


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    login_payload = {
        "username": settings.ADMIN_USERNAME,
        "password": settings.ADMIN_PASSWORD,
    }

    response = await client.post("/auth/login", data=login_payload)

    assert response.status_code == 200, response.text

    data = response.json()

    assert "access_token" in data, "Login response missing access_token"

    token = data["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def member_headers(client: AsyncClient):
    login_payload = {
        "username": "member_user",
        "password": "member_user",
    }

    response = await client.post("/auth/login", data=login_payload)

    assert response.status_code == 200, response.text

    data = response.json()

    assert "access_token" in data, "Login response missing access_token"

    token = data["access_token"]

    return {"Authorization": f"Bearer {token}"}
