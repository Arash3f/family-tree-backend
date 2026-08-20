from dataclasses import dataclass
from uuid import uuid4

from httpx import AsyncClient

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)


@dataclass
class AuthenticatedUser:
    """A freshly created user plus the headers needed to act as them."""

    user: User
    headers: dict[str, str]
    username: str
    password: str


async def create_authenticated_user(
    client: AsyncClient,
    uow: UnitOfWork,
    *,
    permissions: list[str],
    username: str | None = None,
) -> AuthenticatedUser:
    """Create a user holding exactly `permissions` and log them in.

    Logs in over the REST endpoint directly and returns bearer headers, so
    callers building custom-permission actors can wrap them into a type-safe
    GraphQL client via `graphql_auth.gql_client_with_headers`.
    """
    username = username or f"user_{uuid4().hex[:12]}"
    password = f"pw_{uuid4().hex[:16]}"

    permission_ids = []
    for name in permissions:
        permission = await uow.permissions.get_by_name(name)
        if permission is None:
            raise RuntimeError(f"Permission {name!r} is not seeded")
        permission_ids.append(permission.safe_id)

    role = await uow.roles.create(
        Role(name=f"role_{username}", permission_ids=permission_ids)
    )
    user = await uow.users.create(
        User(
            username=username,
            password_hash=Argon2PasswordHasher().hash(password),
            role_id=role.safe_id,
        )
    )
    await uow.commit()

    login = await client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    if login.status_code != 200:
        raise RuntimeError(f"Login failed for {username!r}: {login.text}")

    return AuthenticatedUser(
        user=user,
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        username=username,
        password=password,
    )
