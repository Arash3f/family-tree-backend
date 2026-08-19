from dataclasses import dataclass
from uuid import uuid4

from family_tree_api_client import AuthenticatedClient, Client
from family_tree_api_client.api.auth.login_auth_login_post import (
    asyncio_detailed as login,
)
from family_tree_api_client.models.body_login_auth_login_post import (
    BodyLoginAuthLoginPost,
)
from family_tree_api_client.models.login_response import LoginResponse
from httpx import ASGITransport, AsyncClient

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.infrastructure.services.security.password_hasher_impl import (
    Argon2PasswordHasher,
)


@dataclass
class AuthenticatedUser:
    """A freshly created user plus the client needed to act as them."""

    user: User
    client: AuthenticatedClient
    username: str
    password: str


async def create_authenticated_user(
    client: Client,
    uow: UnitOfWork,
    *,
    permissions: list[str],
    username: str | None = None,
    asgi_transport: ASGITransport,
) -> AuthenticatedUser:
    """Create a user holding exactly `permissions` and log them in.

    Tree isolation can only be tested from a second identity, and the seeded
    admin holds every permission, so tests need a way to mint narrower users.
    Membership is deliberately not granted here: callers decide which trees the
    new user belongs to.
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

    login_response = await login(
        client=client,
        body=BodyLoginAuthLoginPost(username=username, password=password),
    )
    if login_response.status_code != 200:
        raise RuntimeError(f"Login failed for {username!r}: {login_response.content}")

    assert isinstance(login_response.parsed, LoginResponse)
    token = login_response.parsed.access_token

    async_httpx = AsyncClient(
        transport=asgi_transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {token}"},
    )
    authenticated_client = AuthenticatedClient(
        base_url="http://testserver", token=token
    )  # noqa: E501
    authenticated_client.set_async_httpx_client(async_httpx)

    return AuthenticatedUser(
        user=user,
        client=authenticated_client,
        username=username,
        password=password,
    )
