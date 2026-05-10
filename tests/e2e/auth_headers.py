import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.domain.entities.user import User
from app.infrastructure.security.password_hasher_impl import Argon2PasswordHasher
from app.infrastructure.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork


@pytest.fixture
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


@pytest.fixture
async def member_headers(client: AsyncClient, session_factory):
    hasher = Argon2PasswordHasher()
    hashed_password = hasher.hash("member_user")

    async with SQLAlchemyUnitOfWork(session_factory=session_factory) as uow:
        user = User(username="member_user", password_hash=hashed_password)

        await uow.users.create(user)

        await uow.session.flush()

    login_payload = {
        "username": "member_user",
        "password": "member_user",
    }

    response = await client.post("/auth/login", data=login_payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data

    return {"Authorization": f"Bearer {data['access_token']}"}
